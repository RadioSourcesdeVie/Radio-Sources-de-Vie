#!/bin/bash
cd "/c/Users/avena/Desktop/radio sources De Vie"
source .env
python auto_push.py --owm-key "$OWM_KEY" --anthropic-key "$ANTHROPIC_KEY"
