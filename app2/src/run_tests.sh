#!/bin/bash

# Script to run the test suite with options

# Default variables
TEST_TYPE="all"
VERBOSE=0
SKIP_INTEGRATION=0

# Function to display usage
function usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -t, --test-type TYPE    Type of tests to run (api, strategy, candlestick, integration, all)"
    echo "  -v, --verbose           Run with verbose output"
    echo "  -s, --skip-integration  Skip integration tests"
    echo "  -h, --help              Display this help message"
    exit 1
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--test-type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -s|--skip-integration)
            SKIP_INTEGRATION=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown option $1"
            usage
            ;;
    esac
done

# Set up command
CMD="python -m pytest"

# Add verbosity if requested
if [[ $VERBOSE -eq 1 ]]; then
    CMD="$CMD -v"
fi

# Skip integration tests if requested
if [[ $SKIP_INTEGRATION -eq 1 ]]; then
    export SKIP_INTEGRATION_TESTS=1
    echo "Skipping integration tests"
fi

# Add test selection based on type
case "$TEST_TYPE" in
    api)
        CMD="$CMD tests/test_api.py"
        ;;
    strategy)
        CMD="$CMD tests/test_strategies.py"
        ;;
    candlestick)
        CMD="$CMD tests/test_candlestick_patterns.py tests/test_candlestick_strategy.py"
        ;;
    integration)
        CMD="$CMD tests/test_frontend_backend.py"
        ;;
    all)
        CMD="$CMD tests/"
        ;;
    *)
        echo "Error: Unknown test type $TEST_TYPE"
        usage
        ;;
esac

# Run the tests
echo "Running tests: $CMD"
$CMD

# Reset environment variables
unset SKIP_INTEGRATION_TESTS