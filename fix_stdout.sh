#!/bin/bash
# Fix per output silenzioso in proot/Termux Ubuntu
# Riattiva stdout e stderr sul terminale corrente

if [ -t 1 ]; then
  exec 1>/dev/tty 2>&1
  echo "✅ Output terminale ripristinato con successo!"
else
  echo "⚠️ Nessun terminale TTY rilevato, skip fix."
fi
