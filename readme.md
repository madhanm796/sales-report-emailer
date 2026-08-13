# Shopify Automated Hourly Sales Reporter

A Python-based automated sales reporting system that connects to multiple Shopify stores through the **Shopify Admin API**, calculates sales metrics, and sends hourly reports through **Gmail SMTP**.

The project is currently designed for **PythonAnywhere deployment** and supports multiple Shopify brands.

---

## 1. Project Overview

The application currently supports:

- Multiple Shopify stores
- Shopify Admin API authentication using **Client Credentials Grant**
- Automatic Admin API access-token generation
- Hourly sales reporting
- COD order detection
- Partially paid order detection
- Paid order tracking
- Cancelled order tracking
- Refund calculation
- Gross and net sales calculation
- HTML email reports
- Multiple email recipients
- CC recipients
- Dry-run mode
- Logging
- PythonAnywhere Scheduled Tasks

### Current Brands

- Baybee
- Drogo
- Domestica

Additional brands can be added through `config.py` and `.env`.

---

## 2. Current Architecture

```text
                    SHOPIFY STORES
                         │
             ┌───────────┼───────────┐
             │           │           │
           Baybee       Drogo     Domestica
             │           │           │
             └───────────┼───────────┘
                         │
                         ▼
                Shopify Admin API
                         │
                         ▼
                 Python Application
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     Shopify Client  Sales Report   Email Service
          │              │              │
          │              │              ▼
          │              │         Gmail SMTP
          │              │              │
          └──────────────┴──────────────┤
                                         ▼
                                   TO + CC