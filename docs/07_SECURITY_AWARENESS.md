# 7. Security Awareness: Social Engineering and Photo Metadata

> Covers brief sections 37 (Social Engineering Awareness) and 12 (Photo & Metadata Awareness, including the safe local metadata viewer).

## 37. How Oversharing Can Increase Social-Engineering Risk

Social engineering works by building **trust**, **urgency** or **authority**. A scammer who knows real details about you can build all three more easily, because a message that mentions things that are true feels legitimate. Publicly shared context is raw material for that credibility.

| Information category | Why it adds credibility to a scam (conceptually) | Defensive habit |
|---|---|---|
| **Employer** | Messages can claim to be from "IT", "HR" or a known client of your company | Verify workplace requests through official internal channels, never via a link in the message |
| **College / school** | Messages can reference exams, fees, scholarships or a real department | Check with the institution's official portal or office |
| **Travel plans** | "Emergency while abroad" or "your booking has a problem" stories line up with real dates | Share trips after returning; confirm bookings in the official app |
| **Family references** | Impersonating a relative becomes more believable; family names are common security-question answers | Agree on a family verification habit (call back); avoid knowledge-based security answers that are public |
| **Interests** | Fake giveaways, fan pages or offers tailored to what you like | Be sceptical of "you've won" messages; check account verification and age |
| **Public events** | Messages can reference an event you attended ("photos from last night, click here") | Don't open unexpected links; go to the source directly |

### Warning signs in any message
- Urgency or pressure ("act now", "your account will be deleted").
- A request for a **verification code, password or payment**.
- A new or unverified account claiming to be someone you know.
- Links that don't match the organisation's real domain.
- A request to move the conversation to another app, or to keep it secret.

### Defensive rules
1. **Never share verification / OTP codes.** No real service or friend needs them.
2. **Verify out of band.** Call the person on a number you already have.
3. **Go to the source.** Open the official app or type the address yourself instead of clicking.
4. **Reduce the raw material.** The fewer personal details are public, the harder it is to make a convincing pretext.
5. **Report and block** impersonation accounts.

> This project intentionally contains **no example attack messages, templates or scripts**. The goal is recognising and reducing risk.

---

## 12. Photo & Metadata Awareness

### What photos can reveal unintentionally
- **Location context:** street signs, landmarks, house numbers, views from windows.
- **Workplace / school:** logos, uniforms, ID badges and lanyards.
- **Vehicle information:** number plates.
- **Documents:** boarding passes, tickets, letters, ID cards.
- **Computer screens:** open emails, chats, internal tools, passwords on sticky notes.
- **Family information:** children's school names, faces, routines.
- **Travel information:** boarding passes, hotel names, "we're away" timing.

### EXIF metadata (conceptually)
Cameras and phones store extra data **inside the image file**: camera make/model, date and time, settings, and sometimes **GPS latitude/longitude**. It isn't visible in the picture itself. Many social platforms remove it when you upload, but original files shared by **email, messaging apps, cloud links or file transfers** can keep it.

### Safe local metadata viewer: `tools/photo_metadata_viewer.py`

```bash
python tools/photo_metadata_viewer.py my_photo.jpg
python tools/photo_metadata_viewer.py my_photo.jpg --strip my_photo_clean.jpg
```

| Safety property | How |
|---|---|
| Reads metadata **locally** | Uses Pillow on your machine; no network code at all |
| Displays only what exists | Prints tags actually present in the file, with a short privacy note for sensitive ones |
| No hidden inference | Never guesses location from image content; GPS is shown only if the file contains GPS tags |
| No upload | The image never leaves your computer |
| Safe removal | `--strip` rebuilds the image from pixel data into a **new copy**; the original is never modified |

Use it only on **your own** images. Personal images placed in `tools/` are git-ignored so they're never committed by accident.

**Privacy implications:** a single photo with GPS can reveal a home address. A set of photos with timestamps can reveal routines. The camera model and serial number can link photos across accounts.
