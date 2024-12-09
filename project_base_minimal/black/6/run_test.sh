#!/bin/bash
python -m pytest tests/test_black.py
python -m pytest tests/data/comment_after_escaped_newline.py
