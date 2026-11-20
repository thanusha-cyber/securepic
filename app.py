"""SecurePic Studio — redesigned Streamlit image security application."""
import base64
import datetime
import hashlib
import html
from io import BytesIO
from pathlib import Path

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageEnhance

st.set_page_config(page_title="SecurePic | Image Security Studio", layout="wide", initial_sidebar_state="collapsed")

css_path = Path(__file__).parent / "assets" / "style.css"
st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def image_from_bytes(data):
    img = Image.open(BytesIO(data))
    img.load()
    return img


def compare_images(a_bytes, b_bytes):
    """Return annotated comparison, enhanced heatmap, change flag, error and metrics."""
    a = image_from_bytes(a_bytes).convert("RGB")
    b = image_from_bytes(b_bytes).convert("RGB")
    if a.size != b.size:
        return None, None, None, "Image dimensions do not match. Upload two images of the same dimensions.", None
    difference = ImageChops.difference(a, b)
    # Detect perceptible differences without letting a tiny JPEG artifact dominate.
    gray = difference.convert("L")
    raw_mask = gray.point(lambda v: 255 if v > 18 else 0)
    changed_pixels = sum(1 for v in raw_mask.getdata() if v)
    total_pixels = a.width * a.height
    percentage = 100.0 * changed_pixels / max(total_pixels, 1)
    mask = raw_mask.filter(ImageFilter.MaxFilter(5))
    bbox = mask.getbbox()
    highlighted = b.copy().convert("RGBA")
    if bbox:
        overlay = Image.new("RGBA", b.size, (0, 0, 0, 0))
        drawer = ImageDraw.Draw(overlay)
        drawer.rectangle(bbox, fill=(255, 68, 102, 30), outline=(255, 80, 104, 255), width=max(3, min(a.size)//130))
        highlighted = Image.alpha_composite(highlighted, overlay)
    # Dark heatmap: changed pixels glow amber/red; unchanged pixels stay dark.
    intensity = ImageEnhance.Contrast(gray).enhance(2.2)
    heatmap = Image.new("RGB", a.size, (12, 18, 30))
    heat_pixels = heatmap.load(); intensity_pixels = intensity.load()
    for yy in range(a.height):
        for xx in range(a.width):
            v = intensity_pixels[xx, yy]
            if v > 18:
                heat_pixels[xx, yy] = (min(255, 90 + v), min(255, int(v * 0.78)), min(255, int(v * 0.18) + 28))
    return highlighted.convert("RGB"), heatmap, bool(bbox), None, {"changed_pixels": changed_pixels, "total_pixels": total_pixels, "percentage": percentage, "dimensions": a.size}


def report_html(original_name, edited_name, original_bytes, edited_bytes, highlighted, changed):
    buff = BytesIO()
    highlighted.save(buff, format="PNG")
    embedded = base64.b64encode(buff.getvalue()).decode("ascii")
    status = "Changes detected" if changed else "No significant pixel changes detected"
    date = datetime.datetime.now().strftime("%d %B %Y · %I:%M %p")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SecurePic Security Report</title>
<style>body{{margin:0;background:#0c1115;color:#f2f5f1;font-family:Arial,sans-serif;padding:35px 18px}}main{{max-width:850px;margin:auto;background:#172025;border:1px solid #35423d;border-radius:22px;overflow:hidden}}header{{padding:40px;background:#b8f46a;color:#172017}}h1{{font-size:36px;margin:8px 0}}header p{{margin:0}}section{{padding:30px 40px}}.eyebrow{{text-transform:uppercase;letter-spacing:3px;font-size:12px}}.status{{padding:18px;background:#25352c;border-left:4px solid #b8f46a;border-radius:8px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.item{{background:#202b30;border-radius:10px;padding:16px;overflow-wrap:anywhere}}small{{color:#aab8b1}}img{{max-width:100%;border-radius:12px;margin-top:15px}}footer{{padding:20px 40px;color:#aab8b1;border-top:1px solid #35423d}}@media(max-width:600px){{.grid{{grid-template-columns:1fr}}section{{padding:22px}}}}</style></head>
<body><main><header><p class="eyebrow">SECUREPIC / SECURITY INTELLIGENCE</p><h1>Image Integrity Report</h1><p>{html.escape(date)}</p></header><section><p class="eyebrow">01 / RESULT</p><div class="status">{status}</div><p>Pixel comparison uses a tolerance threshold. A clean result does not establish authenticity or provenance.</p><p class="eyebrow">02 / FILE INFORMATION</p><div class="grid"><div class="item"><small>Original file</small><p>{html.escape(original_name)}</p><small>SHA-256</small><p>{hashlib.sha256(original_bytes).hexdigest()}</p></div><div class="item"><small>Compared file</small><p>{html.escape(edited_name)}</p><small>SHA-256</small><p>{hashlib.sha256(edited_bytes).hexdigest()}</p></div></div><p class="eyebrow">03 / VISUAL EVIDENCE</p><img alt="Highlighted comparison" src="data:image/png;base64,{embedded}"><p>Highlighted bounding box shows the area containing detected pixel differences.</p></section><footer>SecurePic Studio · Generated locally from supplied images</footer></main></body></html>'''


def navigate_to(page_name):
    """Navigation callback runs before the radio widget is instantiated."""
    st.session_state["navigation"] = page_name


def section_intro(number, eyebrow, heading, description):
    st.markdown(f'<div class="section-label">{number} / {eyebrow}</div><h2 class="section-heading">{heading}</h2><p class="section-desc">{description}</p>', unsafe_allow_html=True)


def motion_stage(code, kicker, title, accent, subtitle, terms, mode):
    """Reusable CSS-only animated visual stage for every workspace page."""
    import html as _html
    terms = [ _html.escape(t) for t in terms ]
    marquee = "<span class='motion-marquee-item'>" + " &nbsp; ◆ &nbsp; ".join(terms) + " &nbsp; ◆ &nbsp; </span>"
    # Each workspace has a distinct visual sculpture, not a recoloured orbit.
    sculptures = {
        "protect": """<div class='sculpt sculpture-vault' aria-hidden='true'><div class='vault-shadow'></div><div class='vault-cube'><div class='cube-face cube-front'><span class='vault-lock'>⌑</span><small>SECURED</small></div><div class='cube-face cube-back'></div><div class='cube-face cube-left'></div><div class='cube-face cube-right'></div><div class='cube-face cube-top'></div><div class='cube-face cube-bottom'></div></div><div class='vault-scan'></div><span class='sculpt-caption'>AES-STYLE VISUAL / FERNET ENGINE</span></div>""",
        "restore": """<div class='sculpt sculpture-restore' aria-hidden='true'><div class='restore-halo'></div><div class='restore-fragment frag-1'></div><div class='restore-fragment frag-2'></div><div class='restore-fragment frag-3'></div><div class='restore-fragment frag-4'></div><div class='restore-fragment frag-5'></div><div class='restore-fragment frag-6'></div><div class='restore-center'>↺<small>REBUILD</small></div><span class='sculpt-caption'>DIGITAL RECONSTRUCTION</span></div>""",
        "verify": """<div class='sculpt sculpture-verify' aria-hidden='true'><div class='verify-ring vr1'></div><div class='verify-ring vr2'></div><div class='verify-ring vr3'></div><div class='verify-fingerprint'>◎<small>SHA / 256</small></div><div class='verify-beam'></div><span class='sculpt-caption'>SIGNATURE SCAN / BYTE LEVEL</span></div>""",
        "visual-lab": """<div class='sculpt sculpture-lab' aria-hidden='true'><div class='lab-layer lab-back'></div><div class='lab-layer lab-mid'></div><div class='lab-layer lab-front'><span class='lab-target'></span><span class='lab-target second'></span></div><div class='lab-scan'></div><span class='sculpt-caption'>PIXEL DIFFERENCE / LAYER ANALYSIS</span></div>""",
        "reports": """<div class='sculpt sculpture-reports' aria-hidden='true'><div class='report-sheet sheet-back'><i></i><i></i><i></i></div><div class='report-sheet sheet-mid'><i></i><i></i><i></i></div><div class='report-sheet sheet-front'><b>SECUREPIC</b><strong>▥</strong><i></i><i></i><i></i><em>VERIFIED DATA</em></div><span class='sculpt-caption'>EVIDENCE ARCHIVE / EXPORT</span></div>""",
    }
    sculpture = sculptures.get(mode, "")
    st.markdown(f'''<section class="motion-stage motion-{mode}">
      <div class="motion-grid"></div><div class="motion-glow"></div>
      {sculpture}
      <div class="motion-stage-content"><div class="motion-eyebrow"><span class="motion-beacon"></span> {_html.escape(code)} &nbsp; / &nbsp; {_html.escape(kicker)}</div>
      <div class="motion-title">{_html.escape(title)}<br><em>{_html.escape(accent)}</em></div>
      <p class="motion-subtitle">{_html.escape(subtitle)}</p><div class="motion-meta"><span>SECUREPIC / INTERACTIVE WORKSPACE</span><span>● SYSTEM READY</span></div></div>
      <div class="motion-sideword" aria-hidden="true">{_html.escape(mode.upper())}</div>
    </section><div class="motion-marquee" aria-label="Workspace capabilities"><div class="motion-marquee-run">{marquee}{marquee}{marquee}{marquee}</div></div>''',unsafe_allow_html=True)


st.markdown('''<div class="topbar"><span class="brand">SECUREPIC<span class="brand-dot">.</span></span><span class="topbar-right">IMAGE SECURITY STUDIO <span class="live-dot">●</span> LOCAL WORKSPACE</span></div>''', unsafe_allow_html=True)

page = st.radio("Workspace navigation", ["Overview", "Protect", "Restore", "Verify", "Visual Lab", "Reports"], horizontal=True, label_visibility="collapsed", key="navigation")

if page == "Overview":
    st.markdown('''<div class="hero"><div class="hero-orbit"><div class="orb-core"></div><div class="orb-ring orb-ring-one"></div><div class="orb-ring orb-ring-two"></div><div class="orb-ring orb-ring-three"></div><span class="orb-label">SECURE / SCAN / VERIFY</span></div><div class="hero-kicker"><span class="live-dot">●</span> A NEW STANDARD FOR IMAGE TRUST</div><div class="hero-title">Every pixel.<br><span>Protected.</span></div><p class="hero-copy">A thoughtful workspace for encrypting, restoring and examining digital images. Built for clarity. Designed for confidence.</p><div class="hero-index">SECURITY / INTEGRITY / INSIGHT <span>© SECUREPIC STUDIO</span></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="marquee-shell"><div class="marquee-track">ENCRYPTION &nbsp; / &nbsp; IMAGE INTEGRITY &nbsp; / &nbsp; VISUAL FORENSICS &nbsp; / &nbsp; AUTHENTICATED DECRYPTION &nbsp; / &nbsp; EVIDENCE REPORTS &nbsp; / &nbsp; ENCRYPTION &nbsp; / &nbsp; IMAGE INTEGRITY &nbsp; / &nbsp; VISUAL FORENSICS</div></div>', unsafe_allow_html=True)
    section_intro("01", "YOUR WORKSPACE", "Tools for digital trust", "Choose a tool above to begin. Each workflow has its own dedicated space.")
    a,b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown('<div class="card-index">01 / PROTECT</div><div class="card-title">Encrypt your images.</div><p class="card-copy">Turn an image into protected encrypted data and download its private key.</p>', unsafe_allow_html=True)
            st.button("Open encryption", use_container_width=True, on_click=navigate_to, args=("Protect",))
    with b:
        with st.container(border=True):
            st.markdown('<div class="card-index">02 / RESTORE</div><div class="card-title">Bring it back.</div><p class="card-copy">Recover your original image with its encrypted file and matching key.</p>', unsafe_allow_html=True)
            st.button("Open decryption", use_container_width=True, on_click=navigate_to, args=("Restore",))
    a,b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown('<div class="card-index">03 / VERIFY</div><div class="card-title">Check file integrity.</div><p class="card-copy">Compare SHA-256 hashes to identify any difference between two image files.</p>', unsafe_allow_html=True)
            st.button("Open verification", use_container_width=True, on_click=navigate_to, args=("Verify",))
    with b:
        with st.container(border=True):
            st.markdown('<div class="card-index">04 / ANALYSE</div><div class="card-title">See what changed.</div><p class="card-copy">Visualise pixel differences and export an evidence-focused HTML report.</p>', unsafe_allow_html=True)
            st.button("Open visual lab", use_container_width=True, on_click=navigate_to, args=("Visual Lab",))
    st.markdown('<div class="closing-line">BUILT TO MAKE DIGITAL INTEGRITY VISIBLE.</div>', unsafe_allow_html=True)

elif page == "Protect":
    motion_stage('01', 'IMAGE PROTECTION', 'Lock the', 'unseen.', 'A secure space for turning personal images into encrypted files.', ['ENCRYPTION', 'PRIVATE KEYS', 'FERNET SECURITY'], 'protect')
    section_intro("01", "IMAGE ENCRYPTION", "Make your image private.", "Upload a JPG or PNG image. SecurePic encrypts the original file bytes with Fernet authenticated encryption.")
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        with st.container(border=True):
            uploaded = st.file_uploader("Select an image", type=["jpg", "jpeg", "png"], key="protect_upload")
            if uploaded:
                try:
                    raw = uploaded.getvalue(); pic = image_from_bytes(raw)
                    st.image(pic, caption="Original image", use_container_width=True)
                    st.caption(f"{uploaded.name} · {pic.width} × {pic.height} · {len(raw)/1024:.1f} KB")
                except Exception:
                    st.error("This image cannot be opened."); uploaded = None
    with right:
        with st.container(border=True):
            st.markdown('<div class="card-index">ENCRYPTION CONTROL</div><div class="card-title">Protect this file.</div>', unsafe_allow_html=True)
            if st.button("Encrypt image", disabled=uploaded is None, use_container_width=True, type="primary"):
                key = Fernet.generate_key()
                st.session_state.encrypted_result = (Fernet(key).encrypt(uploaded.getvalue()), key, uploaded.name)
            if "encrypted_result" in st.session_state:
                ciphertext, key, original_name = st.session_state.encrypted_result
                st.success(f"Encrypted: {original_name}")
                st.download_button("Download encrypted image", ciphertext, "encrypted_image.bin", "application/octet-stream", use_container_width=True)
                st.download_button("Download secret key", key, "secret.key", "application/octet-stream", use_container_width=True)
                st.warning("Keep your secret key private. Anyone with this key and the encrypted file can decrypt the image.")

elif page == "Restore":
    motion_stage('02', 'IMAGE RECOVERY', 'Bring it', 'back.', 'Restore what belongs to you using your encrypted file and matching key.', ['DECRYPTION', 'ORIGINAL FILE', 'SECURE RESTORE'], 'restore')
    section_intro("02", "IMAGE DECRYPTION", "Restore the original.", "Provide the encrypted .bin file and the matching .key file to recover your image.")
    left,right = st.columns([1,1], gap="large")
    with left:
        with st.container(border=True):
            encrypted = st.file_uploader("Encrypted image (.bin)", type=["bin"], key="restore_bin")
            key_file = st.file_uploader("Secret key (.key)", type=["key"], key="restore_key")
            if st.button("Decrypt image", disabled=not(encrypted and key_file), type="primary", use_container_width=True):
                try:
                    data = Fernet(key_file.getvalue().strip()).decrypt(encrypted.getvalue())
                    img = image_from_bytes(data)
                    extension = (img.format or "PNG").lower()
                    if extension == "jpeg": extension = "jpg"
                    st.session_state.decrypted_result = (data, extension)
                except (InvalidToken, ValueError, TypeError):
                    st.error("Invalid key or encrypted image.")
                except Exception:
                    st.error("Decrypted data is not a supported image.")
    with right:
        with st.container(border=True):
            st.markdown('<div class="card-index">RECOVERED OUTPUT</div><div class="card-title">Your image, restored.</div>', unsafe_allow_html=True)
            if "decrypted_result" in st.session_state:
                data, ext = st.session_state.decrypted_result
                st.image(data, use_container_width=True)
                st.download_button("Download restored image", data, f"decrypted_image.{ext}", "application/octet-stream", use_container_width=True)
            else:
                st.info("Your decrypted image will appear here.")

elif page == "Verify":
    motion_stage('03', 'FILE INTEGRITY', 'Trust the', 'fingerprint.', 'Compare the exact bytes of two files with SHA-256 verification.', ['SHA-256', 'HASH MATCH', 'BYTE INTEGRITY'], 'verify')
    section_intro("03", "HASH VERIFICATION", "Know if a file changed.", "SHA-256 compares the exact file bytes. Different hashes mean the files are not identical.")
    a,b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            original = st.file_uploader("Original image", type=["jpg","jpeg","png"], key="hash_a")
            if original: st.image(original, use_container_width=True)
    with b:
        with st.container(border=True):
            modified = st.file_uploader("Image to verify", type=["jpg","jpeg","png"], key="hash_b")
            if modified: st.image(modified, use_container_width=True)
    if st.button("Compare file hashes", disabled=not(original and modified), type="primary"):
        ah = hashlib.sha256(original.getvalue()).hexdigest(); bh = hashlib.sha256(modified.getvalue()).hexdigest()
        if ah == bh: st.success("Files are byte-for-byte identical.")
        else: st.warning("Different file hashes detected. The files are not identical.")
        st.code(f"ORIGINAL  {ah}\nCOMPARED  {bh}")
    st.caption("Hash comparison detects differences but does not prove whether an image is authentic.")

elif page in ("Visual Lab", "Reports"):
    if page == "Visual Lab":
        motion_stage('04', 'PIXEL INTELLIGENCE', 'Reveal the', 'difference.', 'Explore highlighted regions, thermal maps and changed-pixel metrics.', ['PIXEL ANALYSIS', 'DIFFERENCE MAP', 'VISUAL EVIDENCE'], 'visual-lab')
        section_intro("04", "VISUAL TAMPER LAB", "See beyond the surface.", "Upload two same-sized images to reveal significant pixel differences and a highlighted region.")
    else:
        motion_stage('05', 'EVIDENCE EXPORT', 'Make evidence', 'visible.', 'Turn your comparison into a clear, downloadable image integrity report.', ['FORENSIC REPORT', 'IMAGE EVIDENCE', 'EXPORT HTML'], 'reports')
        section_intro("05", "SECURITY REPORTS", "Evidence, beautifully presented.", "Compare images and export a self-contained HTML analysis report.")
    a,b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            va = st.file_uploader("Original photo", type=["jpg","jpeg","png"], key="visual_a")
            if va: st.image(va, use_container_width=True)
    with b:
        with st.container(border=True):
            vb = st.file_uploader("Edited / comparison photo", type=["jpg","jpeg","png"], key="visual_b")
            if vb: st.image(vb, use_container_width=True)
    if va and vb:
        try:
            result, diff, changed, error, metrics = compare_images(va.getvalue(), vb.getvalue())
            if error: st.warning(error)
            else:
                if changed: st.warning("Significant pixel differences detected.")
                else: st.success("No significant pixel differences detected at the current threshold.")
                m1, m2, m3 = st.columns(3)
                m1.metric("Changed pixels", f"{metrics['changed_pixels']:,}")
                m2.metric("Pixel difference", f"{metrics['percentage']:.2f}%")
                m3.metric("Resolution", f"{metrics['dimensions'][0]} × {metrics['dimensions'][1]}")
                st.markdown('<div class="scan-kicker">LIVE EVIDENCE VIEW / PIXEL-LEVEL INSPECTION</div>', unsafe_allow_html=True)
                x,y = st.columns(2, gap="large")
                with x:
                    st.markdown("#### Highlighted changes")
                    st.image(result, use_container_width=True)
                with y:
                    st.markdown("#### Thermal difference map")
                    st.image(diff, use_container_width=True)
                with st.expander("Explore original and edited evidence", expanded=False):
                    before, after = st.columns(2)
                    with before:
                        st.caption("BEFORE / ORIGINAL")
                        st.image(va, use_container_width=True)
                    with after:
                        st.caption("AFTER / EDITED")
                        st.image(vb, use_container_width=True)
                    st.caption("Difference percentage is based on RGB-to-grayscale pixel difference above a tolerance of 18. It is not a measure of authenticity.")
                if page == "Reports":
                    report = report_html(va.name, vb.name, va.getvalue(), vb.getvalue(), result, changed)
                    st.download_button("Download HTML security report", report, "SecurePic_Report.html", "text/html", type="primary")
        except Exception:
            st.error("One of the uploaded files could not be processed as an image.")
    else:
        st.info("Upload both images to start the comparison.")

st.markdown('<div class="app-footer"><span>SECUREPIC® / IMAGE SECURITY STUDIO</span><span>DESIGNED FOR DIGITAL TRUST · 2026</span></div>', unsafe_allow_html=True)
