package main

import "fmt"
import "log"
import "os"
import "os/exec"


/*
    This is a wrapper module for a Python module 'spt'. The module is available from pip.
    The Go wrapper allows the script to be easily run from the command shell without explicityly calling the python interpreter

    Example: Use spt <some-command> instead of python -m spt <some-command>
*/


func main() {
    cmd_line_args := os.Args[1:]
    if len(cmd_line_args) < 1{
        log.Fatal("Invalid usage. Please see the usage instructions below")
    }
    // out, err := exec.Command("python38", "-m", "spt", "login").Output()
    fmt.Println(cmd_line_args)
    out, err := exec.Command("python38", "-m", "spt", "login").Output()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("The date is %s\n", out)
}