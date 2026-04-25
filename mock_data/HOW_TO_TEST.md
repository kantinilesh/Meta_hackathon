# AI Negotiation Testing Guide

This guide provides exactly what to copy and paste to run a fully realistic testing session in the ContractEnv UI.

## 🏢 STEP 1: Create the Session (As Seller / Acquirer Corp)
Open the app (usually `http://localhost:3000/negotiate`)

1. **Company Name:**
   ```text
   Acquirer Corp
   ```

2. **Company Context / Background Document:**
   ```text
   We are acquiring Startup Inc for $22M. We must ensure we have full ownership of their IP to integrate it into our product line. We also cannot have them competing against us using the knowledge they've gained. We are willing to compromise on duration to get the deal done.
   ```

3. **Contract Text:**
   *(Click "Use Demo NDA" or copy the text from `nda_contract.txt` in this folder)*

4. **Prerequisite Documents (Upload these):**
   - Upload `seller_financials.txt` -> Select **Financials**
   - Upload `seller_due_diligence.txt` -> Select **Due Diligence**
   - Upload `seller_cap_table.txt` -> Select **Cap Table**

5. **Private Constraints:**
   - Use the Quick Template: `+ IP carve-out required` (Deal-Breaker)
   - Add Custom Constraint:
     - Description: `Non-compete cannot exceed 2 years`
     - Category: `Scope`
     - Rule Type: `Max Value`
     - Value matched: `2 years`
     - Deal-breaker: `Checked`

6. **Agent Style:** Select `Balanced`
7. Click **Generate Invite Link &rarr;**
8. (Optional) Save the Documents if prompted.
9. **Copy the Invite Link** to share with the Client.

---

## 🚀 STEP 2: Join the Session (As Client / Startup Inc)
Open the Invite Link in a new incognito window or different browser.

1. **Your Company Name:**
   ```text
   Startup Inc
   ```

2. **Company Context / Background Document:**
   ```text
   We are being acquired by Acquirer Corp. We need this deal to go through, but the founders have extensive pre-existing open-source IP (like DocParser) that MUST NOT be assigned to Acquirer Corp. Also, our founders want to be able to start new non-legal tech businesses in the future, so the non-compete cannot be overly broad or long.
   ```

3. **Prerequisite Documents (If it asks):**
   - Upload `client_financials.txt` -> Select **Financials**
   - Upload `client_ip_assignment.txt` -> Select **IP Assignment**

4. **Private Constraints:**
   - Add Custom Constraint:
     - Description: `Must carve out pre-existing open source IP (DocParser)`
     - Category: `IP`
     - Rule Type: `Must Include`
     - Value matched: `carve-out` or `pre-existing`
     - Deal-breaker: `Checked`
   - Add Custom Constraint:
     - Description: `Non-compete duration must be 12 months or less`
     - Category: `Duration`
     - Rule Type: `Max Value`
     - Value matched: `12 months`
     - Deal-breaker: `Checked`

5. **Agent Style:** Select `Cooperative`
6. Click **Join & Ready &rarr;**

---

## ⚔️ STEP 3: Start the Negotiation
1. Go back to the **Seller's window**.
2. You will see "Client Joined!". Click **Start Negotiation &rarr;**.
3. Watch the two agents use their hidden parameters and the uploaded due diligence/IP registry data to argue clause by clause!
