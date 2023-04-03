#!/bin/bash

# Set variables for the SSH command
jump_host="mayankp@stu.comp.nus.edu.sg"
target_host="xilinx@192.168.95.235"
set pass "plsdonthackus"

# Run SSH command with jump host
ssh -J $jump_host $target_host

expect "$"
send "sudo su - root"

expect "[sudo] password for xilinx: " 
send "$pass"

expect "$ "
send cd ../../home/xilinx
