#!/bin/bash

# Launching redis-server with no persistent storage in background
# Use `redis-cli SHUTDOWN` to stop
redis-server --save "" --appendonly no &