#!/bin/bash

# Script to run single repository investigation locally for testing
# Usage: ./single.sh [REPO_NAME_OR_URL] [force] [model MODEL] [max-tokens NUM] [type TYPE]
# Default repository is "is-odd" if not specified

# Cleanup function to ensure processes are killed on exit
cleanup() {
	local exit_code=$?

	# Kill worker and all its child processes
	if [ -n "$WORKER_PID" ] && kill -0 $WORKER_PID 2>/dev/null; then
		echo "🧹 Stopping worker and child processes (PID: $WORKER_PID)..."
		# Kill the entire process group
		pkill -P $WORKER_PID 2>/dev/null
		kill $WORKER_PID 2>/dev/null
		wait $WORKER_PID 2>/dev/null
	fi

	# Kill temporal server and all its child processes
	if [ -n "$SERVER_PID" ] && kill -0 $SERVER_PID 2>/dev/null; then
		echo "🧹 Stopping Temporal server and child processes (PID: $SERVER_PID)..."
		# Kill the entire process group
		pkill -P $SERVER_PID 2>/dev/null
		kill $SERVER_PID 2>/dev/null
		wait $SERVER_PID 2>/dev/null
	fi

	# Extra safety: Kill any remaining temporal or investigate_worker processes
	pkill -f "temporal server start-dev" 2>/dev/null
	pkill -f "investigate_worker" 2>/dev/null
	pkill -f "uv run python -m investigate_worker" 2>/dev/null

	# Give processes a moment to terminate
	sleep 1

	exit $exit_code
}

# Set trap to always cleanup on exit (success, error, or interrupt)
trap cleanup EXIT INT TERM

# Always load .env.local file for local testing
if [ -f ".env.local" ]; then
	echo "📂 Loading configuration from .env.local..."
	set -a # Export all variables
	source .env.local
	set +a # Stop exporting
	echo "✅ Loaded .env.local"
else
	echo "⚠️  Warning: .env.local not found, using default local settings"
	# Set default environment variables for local testing
	export PROMPT_CONTEXT_STORAGE=file
	export SKIP_DYNAMODB_CHECK=true
	export LOCAL_TESTING=true
fi

echo "Setting up Single Repository Investigation (Local Mode)..."
echo "📝 Environment configured for local testing:"
echo "   PROMPT_CONTEXT_STORAGE=${PROMPT_CONTEXT_STORAGE:-file}"
echo "   SKIP_DYNAMODB_CHECK=${SKIP_DYNAMODB_CHECK:-true}"
echo "   LOCAL_TESTING=${LOCAL_TESTING:-true}"
echo ""

uv sync

# Start Temporal server in background
echo "Starting Temporal server..."
mise run dev-temporal &
SERVER_PID=$!
sleep 5

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
	echo "❌ Error: ANTHROPIC_API_KEY environment variable is not set"
	echo "Please set your Claude API key:"
	echo "export ANTHROPIC_API_KEY='your-api-key-here'"
	exit 1
fi

# Default repository if not specified
DEFAULT_REPO="repo-swarm"
REPO_ARG="${1:-$DEFAULT_REPO}"

# Check if first argument is a special flag (h, help, dry-run, force, etc.)
if [[ $1 == "h" ]] || [[ $1 == "help" ]]; then
	echo "📚 Single Repository Investigation (Local Testing) Help"
	echo ""
	echo "Usage: mise single [REPO_NAME_OR_URL] [ARGUMENTS]"
	echo ""
	echo "Repository Argument:"
	echo "  REPO_NAME_OR_URL                         Repository name from repos.json or direct GitHub URL"
	echo "                                           Default: repo-swarm"
	echo ""
	echo "Arguments (can be used in any order):"
	echo "  force                                    Forces investigation ignoring cache"
	echo "  force-section SECTION_NAME               Force re-execution of specific section"
	echo "  model MODEL_NAME                         Override Claude model to use"
	echo "  max-tokens NUMBER                        Override max tokens (100-100000)"
	echo "  type TYPE                                Override repository type"
	echo "  dry-run                                  Show what would be executed without running"
	echo "  h, help                                  Show this help message"
	echo ""
	echo "Valid Claude models:"
	echo "  claude-3-5-sonnet-20241022 (default)"
	echo "  claude-3-opus-20240229"
	echo "  claude-3-sonnet-20240229"
	echo "  claude-3-haiku-20241022"
	echo ""
	echo "Valid repository types:"
	echo "  generic, backend, frontend, mobile, infra-as-code, libraries"
	echo ""
	echo "Examples:"
	echo "  mise single                                    # Investigate repo-swarm (default)"
	echo "  mise single react                              # Investigate react repository"
	echo "  mise single https://github.com/user/repo      # Direct URL"
	echo "  mise single repo-swarm force                   # Force investigation of repo-swarm"
	echo "  mise single force                              # Force investigation of default (repo-swarm)"
	echo "  mise single force-section monitoring           # Force only monitoring section"
	echo "  mise single model claude-3-haiku-20241022      # Use default repo with different model"
	echo "  mise single repo-swarm type backend max-tokens 5000"
	echo ""
	exit 0
fi

# If first argument is a flag (not a repo), use default repo
if [[ $1 == "force" ]] || [[ $1 == "force-section" ]] || [[ $1 == "dry-run" ]] || [[ $1 == "model" ]] || [[ $1 == "max-tokens" ]] || [[ $1 == "type" ]]; then
	REPO_ARG="$DEFAULT_REPO"
	# Don't shift, process all arguments as flags
	ARGS_TO_PROCESS="$@"
else
	# First argument is the repository, shift it and process the rest
	shift
	ARGS_TO_PROCESS="$@"
fi

echo "🔍 Starting single repository investigation (Local Mode)..."
echo "Repository: $REPO_ARG"

# Parse remaining arguments for configuration overrides
FORCE_FLAG=""
FORCE_SECTION=""
CLAUDE_MODEL=""
MAX_TOKENS=""
REPO_TYPE=""
DRY_RUN=false

# Process arguments
for arg in $ARGS_TO_PROCESS; do
	case "$arg" in
	force)
		FORCE_FLAG="--force"
		echo "🔄 Force mode enabled - will ignore cache"
		;;
	force-section)
		# Next argument should be the section name
		FORCE_SECTION_NEXT=true
		;;
	dry-run)
		echo "🧪 DRY RUN MODE - will not execute investigation"
		DRY_RUN=true
		;;
	model)
		# Next argument should be the model name
		CLAUDE_MODEL_NEXT=true
		;;
	max-tokens)
		# Next argument should be the max tokens value
		MAX_TOKENS_NEXT=true
		;;
	type)
		# Next argument should be the repository type
		REPO_TYPE_NEXT=true
		;;
	*)
		# Check if this is a value for a previous flag
		if [ "$FORCE_SECTION_NEXT" = true ]; then
			FORCE_SECTION="--force-section=$arg"
			echo "🔧 Force section override: $arg"
			FORCE_SECTION_NEXT=false
		elif [ "$CLAUDE_MODEL_NEXT" = true ]; then
			CLAUDE_MODEL="--claude-model=$arg"
			echo "🤖 Using Claude model: $arg"
			CLAUDE_MODEL_NEXT=false
		elif [ "$MAX_TOKENS_NEXT" = true ]; then
			# Validate max tokens
			if ! [[ $arg =~ ^[0-9]+$ ]] || [ "$arg" -lt 100 ] || [ "$arg" -gt 100000 ]; then
				echo "❌ Error: max-tokens must be a number between 100 and 100000"
				kill $SERVER_PID 2>/dev/null
				exit 1
			fi
			MAX_TOKENS="--max-tokens=$arg"
			echo "📝 Using max tokens: $arg"
			MAX_TOKENS_NEXT=false
		elif [ "$REPO_TYPE_NEXT" = true ]; then
			# Validate repository type
			if [[ ! $arg =~ ^(generic|backend|frontend|mobile|infra-as-code|libraries)$ ]]; then
				echo "❌ Error: Invalid repository type: $arg"
				echo "Valid types: generic, backend, frontend, mobile, infra-as-code, libraries"
				kill $SERVER_PID 2>/dev/null
				exit 1
			fi
			REPO_TYPE="--type=$arg"
			echo "📦 Using repository type: $arg"
			REPO_TYPE_NEXT=false
		fi
		;;
	esac
done

# Start the worker in background
echo "Starting Temporal worker..."
cd src && uv run python -m investigate_worker &
WORKER_PID=$!
sleep 3

# Prepare the command
CMD="cd src && uv run python -m client investigate-single \"$REPO_ARG\" $FORCE_FLAG $FORCE_SECTION $CLAUDE_MODEL $MAX_TOKENS $REPO_TYPE"

if [ "$DRY_RUN" = true ]; then
	echo ""
	echo "🧪 DRY RUN - Would execute:"
	echo "   $CMD"
	echo ""
	echo "Configuration:"
	echo "   Repository: $REPO_ARG"
	[ -n "$FORCE_FLAG" ] && echo "   Force: enabled"
	[ -n "$FORCE_SECTION" ] && echo "   Force section: ${FORCE_SECTION#--force-section=}"
	[ -n "$CLAUDE_MODEL" ] && echo "   Model override: ${CLAUDE_MODEL#--claude-model=}"
	[ -n "$MAX_TOKENS" ] && echo "   Max tokens override: ${MAX_TOKENS#--max-tokens=}"
	[ -n "$REPO_TYPE" ] && echo "   Repository type override: ${REPO_TYPE#--type=}"
else
	echo ""
	echo "📊 Configuration:"
	echo "   Repository: $REPO_ARG"
	[ -n "$FORCE_FLAG" ] && echo "   Force: enabled"
	[ -n "$FORCE_SECTION" ] && echo "   Force section: ${FORCE_SECTION#--force-section=}"
	[ -n "$CLAUDE_MODEL" ] && echo "   Model: ${CLAUDE_MODEL#--claude-model=}"
	[ -n "$MAX_TOKENS" ] && echo "   Max tokens: ${MAX_TOKENS#--max-tokens=}"
	[ -n "$REPO_TYPE" ] && echo "   Repository type: ${REPO_TYPE#--type=}"
	echo ""
	echo "Running single repository investigation..."
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	echo ""

	# Run the workflow
	eval $CMD
fi

# Success message (cleanup happens automatically via trap)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Single repository investigation complete!"
echo ""
echo "📊 Investigation Summary:"
echo "   Repository: $REPO_ARG"
echo "   Type: ${REPO_TYPE#--type=}"
[ -n "$CLAUDE_MODEL" ] && echo "   Model: ${CLAUDE_MODEL#--claude-model=}"
echo ""
echo "🎯 What to expect if successful:"
echo "   1. Analysis result saved to temp/[repo-name].arch.md"
echo "   2. Committed to architecture hub repository"
echo "   3. Investigation metadata cached for future runs"
echo ""
echo "📁 Check your results:"
echo "   Local: temp/repos/$REPO_ARG/.arch.md"
echo '   Hub: Check $ARCH_HUB_REPO_NAME (set in .env.local)'
echo ""
echo "💡 First time running? Expected output:"
echo "   - Cloned repository to temp/repos/$REPO_ARG/"
echo "   - Generated .arch.md with sections: overview, modules, data flow, etc."
echo "   - Saved to architecture hub (if configured)"
echo "   - Cached metadata to skip unchanged repos on next run"
echo ""
