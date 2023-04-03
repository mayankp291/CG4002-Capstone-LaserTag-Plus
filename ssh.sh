#!/bin/bash

# Set variables for the SSH command
jump_host="mayankp@stu.comp.nus.edu.sg"
target_host="xilinx@192.168.95.235"

# Run SSH command with jump host
ssh -X -J $jump_host $target_host

