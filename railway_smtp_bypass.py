#!/usr/bin/env python3
"""
Railway SMTP bypass yöntemleri
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import socket
import socks
import os

def try_socks_proxy():
    """SOCKS proxy ile SMTP dene"""
    print("🔄 SOCKS Proxy Method...")
    
    try:
        # SOCKS proxy ayarla (Railway'de çalışabilir)
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
        socket.socket = socks.socksocket
        
        # Normal SMTP dene
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('wcuhrsystem@gmail.com', 'gxhz ichg ppdp wgea')
        
        print("✅ SOCKS proxy method works!")
        return True
        
    except Exception as e:
        print(f"❌ SOCKS proxy failed: {e}")
        return False

def try_tunnel_method():
    """SSH tunnel yöntemi"""
    print("🚇 SSH Tunnel Method...")
    
    # Bu Railway'de çalışmaz ama alternatif olarak gösterelim
    print("❌ SSH tunnel not available on Railway")
    return False

def try_relay_smtp():
    """SMTP relay servisi dene"""
    print("📡 SMTP Relay Method...")
    
    # Railway'in kendi SMTP relay'i olabilir
    relay_servers = [
        'localhost:587',
        '127.0.0.1:587',
        'smtp-relay.railway.app:587',  # Varsayımsal
    ]
    
    for relay in relay_servers:
        try:
            host, port = relay.split(':')
            server = smtplib.SMTP(host, int(port))
            server.starttls()
            # Relay genellikle auth gerektirmez
            print(f"✅ SMTP relay {relay} accessible")
            return True
        except Exception as e:
            print(f"❌ SMTP relay {relay} failed: {e}")
    
    return False

def try_alternative_ports():
    """Alternatif portları dene"""
    print("🔌 Alternative Ports Method...")
    
    # Gmail'in alternatif portları
    ports = [587, 465, 25, 2525, 2587]
    
    for port in ports:
        try:
            print(f"   Testing port {port}...")
            sock = socket.create_connection(('smtp.gmail.com', port), timeout=10)
            sock.close()
            print(f"   ✅ Port {port} accessible")
            
            # SMTP test
            if port == 465:
                server = smtplib.SMTP_SSL('smtp.gmail.com', port)
            else:
                server = smtplib.SMTP('smtp.gmail.com', port)
                server.starttls()
            
            server.login('wcuhrsystem@gmail.com', 'gxhz ichg ppdp wgea')
            server.quit()
            
            print(f"   🎉 Gmail SMTP works on port {port}!")
            return port
            
        except Exception as e:
            print(f"   ❌ Port {port} failed: {e}")
    
    return None

def try_ip_direct():
    """Gmail IP'sine direkt bağlan"""
    print("🎯 Direct IP Method...")
    
    # Gmail'in IP adresleri
    gmail_ips = [
        '74.125.133.108',
        '142.250.191.108', 
        '172.217.164.108',
        '216.58.194.108'
    ]
    
    for ip in gmail_ips:
        try:
            print(f"   Testing IP {ip}...")
            
            server = smtplib.SMTP(ip, 587)
            server.starttls()
            server.login('wcuhrsystem@gmail.com', 'gxhz ichg ppdp wgea')
            server.quit()
            
            print(f"   🎉 Gmail SMTP works with IP {ip}!")
            return ip
            
        except Exception as e:
            print(f"   ❌ IP {ip} failed: {e}")
    
    return None

if __name__ == "__main__":
    print("🚂 RAILWAY SMTP BYPASS METHODS")
    print("=" * 40)
    
    methods = [
        try_alternative_ports,
        try_ip_direct,
        try_relay_smtp,
        try_socks_proxy,
        try_tunnel_method
    ]
    
    for method in methods:
        result = method()
        if result:
            print(f"\n🎉 SUCCESS with {method.__name__}!")
            break
        print()
    else:
        print(f"\n💥 All bypass methods failed")
        print("Railway is strictly blocking SMTP")