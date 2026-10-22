#!/usr/bin/env python3
"""Tạo salt + PBKDF2 hash cho Streamlit Secrets (không in lại mã bí mật)."""
import getpass, secrets, hashlib
pin = getpass.getpass("Nhập mã truy cập mạnh cho tài khoản: ")
if len(pin) < 10:
    raise SystemExit("Cần tối thiểu 10 ký tự để giảm rủi ro đoán mã.")
salt=secrets.token_hex(16)
digest=hashlib.pbkdf2_hmac("sha256",pin.encode("utf-8"),bytes.fromhex(salt),390000).hex()
print("salt = \""+salt+"\"")
print("hash = \""+digest+"\"")
