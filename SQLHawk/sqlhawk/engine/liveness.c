/*
 * SQLHawk liveness engine
 * ========================
 * Small, fast, multi-threaded TCP connect-check used as a pre-flight
 * step before the (slower) Python crawler/injector run against a
 * target. Given a host and a list of ports, it reports which ports
 * accept a TCP connection, so the rest of the toolkit doesn't waste
 * time crawling a dead host.
 *
 * This does NOT send any exploit payloads — it only performs a plain
 * TCP connect() (the same thing a browser does before an HTTP
 * request), so it's safe to use as a lightweight reachability check.
 *
 * Build:
 *   gcc -O2 -pthread -o liveness liveness.c
 *
 * Usage:
 *   ./liveness <host> <port1> [port2] [port3] ...
 *
 * Output (one line per port):
 *   <port> open
 *   <port> closed
 */

#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define CONNECT_TIMEOUT_SEC 3

typedef struct {
    char host[256];
    int port;
    int is_open;
} PortCheck;

static void *check_port(void *arg) {
    PortCheck *pc = (PortCheck *)arg;

    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    char port_str[8];
    snprintf(port_str, sizeof(port_str), "%d", pc->port);

    if (getaddrinfo(pc->host, port_str, &hints, &res) != 0) {
        pc->is_open = 0;
        return NULL;
    }

    int sock = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sock < 0) {
        freeaddrinfo(res);
        pc->is_open = 0;
        return NULL;
    }

    struct timeval tv;
    tv.tv_sec = CONNECT_TIMEOUT_SEC;
    tv.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    int result = connect(sock, res->ai_addr, res->ai_addrlen);
    pc->is_open = (result == 0);

    close(sock);
    freeaddrinfo(res);
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <host> <port1> [port2] ...\n", argv[0]);
        return 1;
    }

    const char *host = argv[1];
    int num_ports = argc - 2;

    PortCheck *checks = calloc(num_ports, sizeof(PortCheck));
    pthread_t *threads = calloc(num_ports, sizeof(pthread_t));

    if (!checks || !threads) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    for (int i = 0; i < num_ports; i++) {
        strncpy(checks[i].host, host, sizeof(checks[i].host) - 1);
        checks[i].port = atoi(argv[i + 2]);
        pthread_create(&threads[i], NULL, check_port, &checks[i]);
    }

    for (int i = 0; i < num_ports; i++) {
        pthread_join(threads[i], NULL);
        printf("%d %s\n", checks[i].port, checks[i].is_open ? "open" : "closed");
    }

    free(checks);
    free(threads);
    return 0;
}
