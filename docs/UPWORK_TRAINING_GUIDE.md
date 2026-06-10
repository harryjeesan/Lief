# Leif Training Guide: Dominating Upwork

To turn Leif into the ultimate freelance assistant, we need to fine-tune her on the exact types of jobs that pay well on Upwork and are easily accelerated by AI. 

This document serves as your "Curriculum" for training Leif. By having the conversations outlined below over the next two weeks, you will seed her SQLite database (`leif_memory.db`) with the perfect data. When we run the Phase 2 export script and fine-tune her in Phase 3, she will permanently internalize these skills.

---

## Part 1: High-Value Upwork Niches for AI Acceleration

The secret to making money with AI on Upwork isn't taking massive, complex 6-month enterprise projects. The secret is taking **$100 to $500 micro-projects** that normally take a developer 3 days to build, and completing them in **3 hours** using Leif.

Here are the top 4 niches Leif will excel at once trained:

### 1. API Integrations & Webhooks (Average Pay: $150 - $400)
**The Job:** A client has two pieces of software (e.g., Shopify and Google Sheets, or a custom CRM and Stripe) and needs them to talk to each other.
**Why Leif wins:** Writing Python/FastAPI scripts to catch webhooks, parse JSON, and send API requests is highly repetitive. Leif can write 90% of this boilerplate instantly.

### 2. Internal Dashboards & Admin Panels (Average Pay: $300 - $800)
**The Job:** A small business needs a clean web interface to view their database, track sales, or manage employees.
**Why Leif wins:** React + Tailwind CSS allows for rapid UI development. You can ask Leif to scaffold the dashboard layout, data tables, and charts, leaving you to just wire up the real data.

### 3. Data Scraping & Automation Scripts (Average Pay: $50 - $250)
**The Job:** A client needs a script to scrape a website every day, or a Python macro to automate a boring spreadsheet task.
**Why Leif wins:** Leif already has Playwright subagent capabilities. She can write scraping scripts and DOM parsing logic faster than any human.

### 4. Code Auditing & Bug Fixing (Average Pay: $50 - $150 / hr)
**The Job:** A client's previous freelancer disappeared, leaving them with broken React or Python code. They need someone to fix it.
**Why Leif wins:** You paste the broken code to Leif. She finds the race conditions, syntax errors, or logical flaws, rewrites it cleanly, and you deliver the fix the same day.

---

## Part 2: The Training Conversations (Seeding the Database)

To train Leif, you need to simulate these jobs. Copy and paste the prompts below into your chat with Leif. **Crucially: if her answer isn't perfect, tell her to fix it.** The correction is what trains her to code *your* way.

### Training Set 1: API Integrations
**Prompt A:** 
> "Leif, act as my freelance assistant. We just got a client who needs a FastAPI endpoint that receives a Stripe webhook for a 'checkout.session.completed' event. Write the endpoint, verify the Stripe signature, and print the customer email."

**Prompt B:**
> "The client also needs us to take that email and add it to a Mailchimp audience via their API. Write the Python function to do this using the `requests` library."

### Training Set 2: The React Dashboard
**Prompt A:**
> "Leif, I need to build an internal admin dashboard for a client using React and Tailwind CSS. Scaffold a responsive sidebar navigation menu and a main content area."

**Prompt B:**
> "Now, write a reusable React component for a Data Table. It should accept an array of objects as props and render a clean, striped table. Ensure it handles empty states gracefully."

### Training Set 3: Bug Fixing (The "Fix it" reflex)
**Prompt A:**
> "Leif, a client gave me this broken React code. It's supposed to fetch user data on mount, but it's causing an infinite loop. Here is the code: 
> `useEffect(() => { fetchUser(id).then(setData) }, [data])`
> Explain why it's broken to me simply so I can tell the client, and then give me the fixed code."

### Training Set 4: Client Communication (Soft Skills)
**Prompt A:**
> "Leif, I just finished the Stripe integration for the client. Write a polite, professional message to the client telling them the job is done, how to test it, and asking them to review the work and release the milestone payment. Keep it friendly but concise."

---

## Part 3: The Golden Rule of Fine-Tuning

A fine-tuned model is only as good as the data it trains on.

If you ask Leif to build a React component and she uses `var` instead of `const`, or doesn't use the styling you prefer: **Do not just accept it and rewrite it yourself.**

Instead, tell her:
> *"No, do not use `var`. Use modern ES6 syntax, and prefer Tailwind utility classes."*

When she corrects herself and gives you the perfect answer, **that exchange is saved in `leif_memory.db`**. When we export the data in Phase 2 and fine-tune her in Phase 3, the model's weights will physically shift to prefer ES6 syntax and Tailwind. 

She will literally evolve to write code exactly the way you want it written.

---

## Part 4: The "Synthetic Data" Hack (Using ChatGPT/Claude/Gemini)

If you don't want to manually type out 50 to 100 conversations with Leif over the next two weeks, you can use **Synthetic Data Generation**. 

You can ask a massive, ultra-smart model (like Claude 3.5 Sonnet or ChatGPT-4o) to generate perfect "User vs AI" dialogues for Upwork jobs. You then literally just copy the User's question, paste it to Leif, and let Leif answer it so it goes into her database. If Leif gets it wrong, you copy the perfect answer from Claude, paste it to Leif, and say "No, do it exactly like this: [paste code]".

Here is the exact master prompt you can copy and paste into ChatGPT/Claude/Gemini right now to generate the training data:

### The Master Prompt for Synthetic Generation
> **Copy and paste this into ChatGPT, Claude, or Gemini:**
> 
> "I am fine-tuning a local AI coding assistant to help me execute $100-$500 freelance micro-projects on Upwork. The assistant will be built on a 3-Billion parameter local model, so it needs very clean, highly-structured examples of how to answer freelancing queries perfectly.
>
> Please generate 5 distinct 'User' vs 'Assistant' coding interactions. 
> 
> **The Rules for the interactions:**
> 1. The niches should be: API/Webhook integration, React Admin Dashboards, Python Automation Scripts, and Code Auditing.
> 2. The User prompt should simulate a freelancer asking for help with a specific client requirement.
> 3. The Assistant response MUST be perfect. It must include zero fluff, immediately provide the exact terminal commands to scaffold the project, and output highly modular, production-ready code (using modern ES6/React or Python/FastAPI). 
> 4. The Assistant should use Tailwind CSS for UI tasks.
> 
> Output the 5 interactions clearly separated so I can read them."

### How to Feed the Results to Leif
Once ChatGPT/Claude gives you the 5 interactions:
1. Copy the "User" prompt from ChatGPT.
2. Paste it into Leif's chat UI.
3. If Leif gives a great answer, great! It's saved in the database.
4. If Leif gives a bad answer, reply to Leif: *"No, that's not quite right. Rewrite it exactly like this: [Paste the 'Assistant' response you got from ChatGPT]"*
5. Leif will reply acknowledging the correction. That perfectly corrected exchange is now safely stored in your `leif_memory.db` for fine-tuning!
