from fpdf import FPDF

# Demo NDA
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=15, style='B')
pdf.cell(200, 10, txt="Mutual Non-Disclosure Agreement (NDA)", ln=1, align='C')
pdf.set_font("Arial", size=11)
pdf.ln(10)
nda_text = """This Mutual Non-Disclosure Agreement is entered into by and between the parties.

1. Definition of Confidential Information
"Confidential Information" means any proprietary information, technical data, trade secrets or know-how, including, but not limited to, research, product plans, products, services, customer lists, and markets.

2. Non-Compete
The Receiving Party agrees not to engage in any business activity that competes with the Disclosing Party's current or future products for a period of 5 years globally.

3. IP Assignment
Any ideas, inventions, or improvements conceived during discussions shall be assigned exclusively to the Disclosing Party without additional compensation.

4. Liability Cap
The maximum liability for any breach of this agreement shall be capped at $1,000,000.

5. Jurisdiction
This agreement shall be governed by the laws of the State of Delaware."""

pdf.multi_cell(0, 8, txt=nda_text)
pdf.output("Demo_NDA_Agreement.pdf")

# Demo SaaS
pdf2 = FPDF()
pdf2.add_page()
pdf2.set_font("Arial", size=15, style='B')
pdf2.cell(200, 10, txt="Software as a Service (SaaS) Agreement", ln=1, align='C')
pdf2.set_font("Arial", size=11)
pdf2.ln(10)
saas_text = """This SaaS Agreement governs the use of the Provider's cloud software.

1. Scope of License
Provider grants Customer a non-exclusive, non-transferable, worldwide license to use the Software solely for internal business operations.

2. Payment Terms
Customer shall pay all fees within 30 days of invoice receipt (Net-30). Late payments incur a 1.5% monthly interest rate.

3. Data Ownership
Customer retains all rights to data uploaded to the service. Provider is granted a limited license to process data to provide the service.

4. Termination for Convenience
Either party may terminate this agreement at any time by providing 90 days written notice to the other party.

5. Service Level Agreement (SLA)
Provider guarantees 99.9% uptime. Failure to meet this SLA will result in a 10% service credit for the affected month."""

pdf2.multi_cell(0, 8, txt=saas_text)
pdf2.output("Demo_SaaS_Agreement.pdf")
print("PDFs generated.")
