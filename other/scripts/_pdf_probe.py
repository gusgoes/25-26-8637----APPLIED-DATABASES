from pypdf import PdfReader

p = r"C:/Users/gusgo/OneDrive/Desktop/Final Project Specification 2026.pdf"
t = "\n".join((pg.extract_text() or "") for pg in PdfReader(p).pages)

keys = [
    "Description",
    "Marks",
    "Marking Scheme",
    "Plagiarism",
    "Submission",
    "Python Application",
    "Databases",
    "Main Menu",
    "View Speakers & Sessions",
    "View Attendees by Company",
    "Add New Attendee",
    "View Connected Attendees",
    "Add Attendee Connection",
    "View Rooms",
    "Exit Application",
    "Anything Else",
    "Error Conditions",
]

for k in keys:
    i = t.lower().find(k.lower())
    if i != -1:
        s = max(0, i - 250)
        e = min(len(t), i + 700)
        print("\n" + ("=" * 20) + f" {k} " + ("=" * 20))
        print(t[s:e].replace("\n", " "))
