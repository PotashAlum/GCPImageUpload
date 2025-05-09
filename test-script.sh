#!/bin/bash
# run_tests.sh
# Script to run tests with various options

# Default values
TEST_TYPE="all"
COVERAGE=false
VERBOSITY="-v"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSITY="-vv"
            shift
            ;;
        --quiet)
            VERBOSITY=""
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --unit        Run only unit tests"
            echo "  --integration Run only integration tests"
            echo "  --e2e         Run only end-to-end tests"
            echo "  --coverage    Generate test coverage report"
            echo "  --verbose     Show more detailed test output"
            echo "  --quiet       Show minimal test output"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $key"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Determine which tests to run
case $TEST_TYPE in
    "unit")
        TEST_PATH="tests/unit"
        ;;
    "integration")
        TEST_PATH="tests/integration"
        ;;
    "e2e")
        TEST_PATH="tests/e2e"
        ;;
    "all")
        TEST_PATH="tests"
        ;;
esac

# Set up command
if [ "$COVERAGE" = true ]; then
    CMD="pytest $VERBOSITY --cov=. --cov-report=term --cov-report=html $TEST_PATH"
else
    CMD="pytest $VERBOSITY $TEST_PATH"
fi

# Run tests
echo "Running $TEST_TYPE tests..."
echo "Command: $CMD"
eval $CMD

# Display coverage report location if generated
if [ "$COVERAGE" = true ]; then
    echo "Coverage report generated in htmlcov/ directory"
    echo "Open htmlcov/index.html in a browser to view the report"
fi
