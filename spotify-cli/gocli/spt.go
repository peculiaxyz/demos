package sptwrapper

import (
	"fmt"
	"log"
	"os"
	"os/exec"
)

/*
   This is a wrapper module for a Python module 'spt'. The module is available from pip.
   The Go wrapper allows the script to be easily run from the command shell without explicityly calling the python interpreter

   Example: Use spt <some-command> instead of python -m spt <some-command>
*/
const PYTHON3_ENV = "PYTHON3_EXE"
const DEFAULT_PYTTHON3_EXE = "python38" // Make sure that this python is included in your PATH

func getCLIUsageInstructions() string {
	print_help_args := []string{"-m", "spt", "--help"}
	usage_msg, err := exec.Command(os.Getenv(PYTHON3_ENV), print_help_args...).Output()

	if err != nil {
		log.Fatal(err)
	}
	result := string(usage_msg)
	return result
}

func validateCLIArguments(args []string) {
	if len(args) < 1 {
		fmt.Println(getCLIUsageInstructions())
		log.Fatal("Invalid usage. Please see the usage instructions above\n")
	}

}

func executePython(args []string) {
	// Runs the spt python 3 script which should be installed in the default package directory using pip
	out, err := exec.Command(os.Getenv(PYTHON3_ENV), args...).Output()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(out)
}

func setupPythonExe() {
	_, ok := os.LookupEnv(PYTHON3_ENV)
	if !ok {
		os.Setenv(PYTHON3_ENV, DEFAULT_PYTTHON3_EXE)
	} // Else,...
}

func main() {
	setupPythonExe()
	
	cmd_line_args := os.Args[1:]
	default_args := []string{"-m", "spt"}

	validateCLIArguments(cmd_line_args)
	python_script_args := append(default_args, cmd_line_args...)
	executePython(python_script_args)
}
