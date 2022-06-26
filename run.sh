#!/bin/bash

run_redis() {
    docker run -itd --name redis -p 127.0.0.1:6379:6379 redis
}

stop_redis() {
    docker stop redis
    docker rm redis
}

main() {
    case $1 in
        run_redis)
            run_redis
            ;;
        stop_redis)
            stop_redis
            ;;
        *)
            echo "Usage: $0 {run|stop}"
            exit 1
            ;;
    esac
}

main $@
