# Demo Script — Rural SACCO OneStop Solutions

*Say this, verbatim, in front of a SACCO committee. 8 minutes.*

---

## 1. Open (30 seconds)

> "Before I show you software, one question. How many hours did your treasurer spend last month matching M-Pesa messages to member passbooks?"
>
> *(Wait for the answer. It's usually "a whole weekend" or "two weeks.")*
>
> "That number is about to become zero."

## 2. The dashboard (1 minute)

Open `http://localhost:5000` and log in as `admin / admin123`.

> "This is what your manager sees. Four numbers, one screen. Members, savings, loan book, and — **the most important number** — the M-Pesa match rate. Right now it says 82.5%. Every green row on the table below is a deposit the system matched to a member **automatically**. Every red row is one that needs five seconds of human attention. No Excel. No paper."

## 3. A real member (1 minute)

Click **Members**, then click the top member.

> "This is member RSC-1007. Trust Score 92, Rank A. The bars show you *why*: 40/40 on repayment, 20/20 on savings, 15/15 on attendance. That's not an opinion — that's what her data says.
>
> And this on the right — Rank A means she can borrow 3× her savings, no guarantor, 10% interest, 24 months. **We can defend her approval to a regulator with evidence, not with a handshake.**"

## 4. The problem member (1 minute)

Search `RSC-` and click a Rank D or E member.

> "Here's member RSC-1023. Score 34, blacklisted. Why? 45 days overdue on a loan, no deposits in 8 months. **The system flagged her 45 days ago** — before your treasurer noticed. Rank E means: no new loans, no guarantors can back her. That's not me being cruel. That's protecting the other 49 members' savings."

## 5. AGM PDF (1 minute)

Click **AGM PDF** in the top navbar. PDF downloads.

> "This is your AGM pack. Executive summary, rank distribution, top savers, aging report, open risks. Every number pulled live from the database. **The document your auditor asks for is a single click away.** This used to take your secretary three days."

## 6. The member side (2 minutes)

Ask for a member's phone. Dial the USSD shortcode (in demo, run the USSD tests in terminal):

> "This works on any phone. A KES 1,500 Itel. No data bundle. No app. The member dials the code, presses 1, and hears — in Kiswahili if they prefer — *'Salio lako ni KES 3,200.'* Every transaction sends an SMS receipt with a reference. **No member ever argues about their balance again.**"

## 7. The price objection (1 minute)

> "Existing SACCO software charges KES 12,000 per year for 30 members. This system charges per *active* member. For a 50-member SACCO, that's about **KES 500 per month**. One reconciled M-Pesa deposit per day pays for it."

## 8. The close (30 seconds)

> "What I'm asking for is not a purchase. It's a **two-week trial with your real data**. You keep your current system running. On day one we import last year's M-Pesa and see how many deposits the system matches. If that number isn't 95% or higher, you owe me nothing. If it is, we go live.
>
> **Your members' savings deserve a system that works on their phone, in their language, with their real money.** That's what this is."

---

## Common objections & answers

**"Our treasurer is not computer-literate."**
> "The manager console is one screen with three colours. If your treasurer can read green, red, and amber, they can run this."

**"What if the internet goes down?"**
> "The system runs on your laptop, offline. It syncs when the internet comes back. No internet, no problem — the treasurer keeps entering data, the system keeps matching M-Pesa as it arrives."

**"What if M-Pesa refunds a member?"**
> "Every M-Pesa transaction is stored in its own table with the raw payload. Refunds are matched to the original deposit by `TransID`. The audit trail shows both sides."

**"How much does it cost?"**
> "KES 500 per month for a 50-member SACCO. KES 12,000 for a 500-member DT-SACCO. One M-Pesa reconciliation per day covers it."

**"What about our data — is it safe?"**
> "Your data lives on your laptop and on your GitHub backup. We never see it. If you want a formal data processing agreement aligned with the ODPC, we sign one before day one."

**"Can I see the code?"**
> "Yes. github.com/Wakali-Ian/rural-sacco-onestop. MIT licensed. Every line auditable. **The code that runs your SACCO is public and reproducible.**"

---

## The 3-line close, if you only have 30 seconds

> "Your members save on feature phones, but your SACCO runs on paper. We close that gap with USSD, M-Pesa auto-reconciliation, and a trust score that turns 3 years of savings history into loan decisions. **Two weeks with your real data, 95% match rate or it's free.**"
