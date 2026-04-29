from pypdf import PdfReader

p = r"C:/Users/gusgo/OneDrive/Desktop/Final Project Specification 2026.pdf"
t = "\n".join((pg.extract_text() or "") for pg in PdfReader(p).pages)

keys = [
    "2.1.1 Plagiarism",
    "3 Submission",
    "3.1 Python Application",
    "3.1.1 Databases",
    "3.1.2 Main Menu",
    "3.1.3 1 (View Speakers & Sessions)",
    "3.1.4 2 (View Attendees by Company)",
    "3.1.5 3 (Add New Attendee)",
    "3.1.6 4 (View Connected Attendees)",
    "3.1.7 5 (Add Attendee Connection)",
    "3.1.8 6 (View Rooms)",
    "3.1.9 x (Exit Application)",
    "3.1.10 Anything Else",
]

for k in keys:
    i = t.rfind(k)
    if i != -1:
        s = max(0, i - 120)
        e = min(len(t), i + 1200)
        print("\n" + ("=" * 20) + f" {k} " + ("=" * 20))
        print(t[s:e])
