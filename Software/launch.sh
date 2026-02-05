#!/bin/bash
# ============================================
#  Launch script for SmartVision application
#  Author: Andresse Bassinga
#  Description: Quick alias to launch Software.App.main
# ============================================

# Get parent current directory
parent_dir="$(dirname "$PWD")"

# Set aliases
alias run_app="cd \"$parent_dir\" && python3 -m Software.App.main"
alias show_video="cd \"$parent_dir\" && python3 -m Software.Tools.debug_display"

echo "✅ Launch alias 'run_app and show_video' has been loaded."
echo "You can now type: run_app"
echo "You can now type: show_video"