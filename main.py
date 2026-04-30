import streamlit as st
import pandas as pd
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Streamlit UI Setup
st.set_page_config(page_title="📬 Send Emails with Inline Images", layout="wide")
st.title("📬 Send Emails with Embedded Images (CID Method)")

# Gmail credentials input
st.subheader("🔐 Gmail Login (Use App Password)")
sender_email = st.text_input("Sender Gmail Address", placeholder="you@gmail.com")
password = st.text_input("Gmail App Password", type="password", help="Use an app password, not your Gmail password.")

# Email content input
st.markdown("---")
st.subheader("📨 Email Content")
subject = st.text_input("Email Subject")
raw_html = st.text_area("HTML Body", height=300, placeholder="Use {{image1}}, {{image2}}, etc. to embed uploaded images.")

# Upload images to embed
st.markdown("---")
st.subheader("🖼️ Upload Images to Embed (CID Method)")
uploaded_files = st.file_uploader("Upload multiple images", type=["png", "jpg", "jpeg", "gif"], accept_multiple_files=True)

# Prepare images for embedding
cid_images = []
if uploaded_files:
    for idx, file in enumerate(uploaded_files, start=1):
        cid = f"image{idx}"
        cid_images.append((cid, file))
        st.markdown(f"**Use `{{{{image{idx}}}}}`** to insert this image:")
        st.image(file, width=250)

# Replace CID placeholders with proper HTML
html_body = raw_html
for cid, _ in cid_images:
    html_body = html_body.replace(f"{{{{{cid}}}}}", f'<img src="cid:{cid}">')

# Upload recipient list (CSV)
st.markdown("---")
st.subheader("📋 Upload Recipients (CSV File)")
data_file = st.file_uploader("Upload a CSV file with at least one column containing email addresses", type=["csv"])

receiver_emails = []
if data_file:
    df = pd.read_csv(data_file)
    st.dataframe(df)
    email_column = st.selectbox("Select the email column", df.columns)
    receiver_emails = df[email_column].dropna().unique().tolist()
    st.success(f"✅ Loaded {len(receiver_emails)} email(s).")

# Function to send email
def send_email_with_cid(sender_email, receiver_list, password, html_body, subject):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        try:
            server.login(sender_email, password)
        except smtplib.SMTPAuthenticationError as e:
            st.error("❌ Authentication failed. Make sure you're using a valid Gmail App Password.")
            return

        for i, receiver in enumerate(receiver_list):
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = receiver

            # Attach HTML
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(html_body, "html"))
            msg.attach(alt)

            # Attach each image with CID
            for cid, file in cid_images:
                file.seek(0)
                img = MIMEImage(file.read())
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=file.name)
                msg.attach(img)

            try:
                server.sendmail(sender_email, receiver, msg.as_string())
                st.success(f"{i + 1}. ✅ Email sent to {receiver}")
            except Exception as e:
                st.error(f"{i + 1}. ❌ Failed to send to {receiver}: {e}")

# Send button
st.markdown("---")
if st.button("🚀 Send Emails"):
    if not sender_email or not password or not subject or not raw_html:
        st.error("⚠️ Please fill in all required fields.")
    elif not receiver_emails:
        st.error("⚠️ Please upload a valid CSV with email addresses.")
    else:
        send_email_with_cid(sender_email, receiver_emails, password, html_body, subject)
