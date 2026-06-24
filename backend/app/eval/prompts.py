"""
Evaluation Prompts Dataset
===========================
Contains 10 real product prompts and 10 edge-case prompts (vague, conflicting, incomplete).
"""

REAL_PROMPTS = [
    {
        "id": "real-crm",
        "name": "CRM with Role Access & Payments",
        "prompt": "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
    },
    {
        "id": "real-blog",
        "name": "Personal Blog with Comments",
        "prompt": "Create a personal blog where an admin can write, edit, and delete posts. Regular users can sign up, read posts, and leave comments."
    },
    {
        "id": "real-ecommerce",
        "name": "E-Commerce Shop",
        "prompt": "Build an e-commerce platform with a product catalog, search functionality, shopping cart, customer checkout flow, and merchant order management dashboard."
    },
    {
        "id": "real-booking",
        "name": "Doctor Appointment Booking",
        "prompt": "Build a medical clinic booking app. Patients can view doctor schedules, book appointments, and pay fees. Doctors can view patient files and update status."
    },
    {
        "id": "real-lms",
        "name": "Learning Management System",
        "prompt": "Build an LMS portal where instructors can upload courses, lessons, and quizzes. Students can enroll, track their progress, and take quizzes."
    },
    {
        "id": "real-helpdesk",
        "name": "IT Help Desk ticketing",
        "prompt": "Create a help desk system where customers submit support tickets. Support agents can assign tickets, update status (open, pending, closed), and reply."
    },
    {
        "id": "real-fitness",
        "name": "Fitness & Workout Tracker",
        "prompt": "Build a fitness tracker where users log daily workouts, exercises, reps, and weights. Users can view progress charts and set weekly goals."
    },
    {
        "id": "real-inventory",
        "name": "Warehouse Inventory Manager",
        "prompt": "Build an inventory management system. Managers can add products, track stock counts, set low-stock alerts, and log supplier shipments."
    },
    {
        "id": "real-expense",
        "name": "SaaS Expense Tracker",
        "prompt": "Build a company expense manager. Employees submit expense receipts, managers approve or reject them, and finance admins view aggregated reports."
    },
    {
        "id": "real-realestate",
        "name": "Property Listing Portal",
        "prompt": "Create a real estate portal. Agents can list properties with prices, locations, and photos. Buyers can search, filter by price range, and submit inquiry messages."
    }
]

EDGE_CASE_PROMPTS = [
    # ── Vague Prompts ──────────────────────────────────────────────────────────
    {
        "id": "edge-vague-1",
        "name": "Extremely Vague App Request",
        "type": "vague",
        "prompt": "make a web app"
    },
    {
        "id": "edge-vague-2",
        "name": "Vague Tool Request",
        "type": "vague",
        "prompt": "Build something cool for my business"
    },
    {
        "id": "edge-vague-3",
        "name": "One Word CRM Request",
        "type": "vague",
        "prompt": "CRM"
    },
    {
        "id": "edge-vague-4",
        "name": "Vague System Request",
        "type": "vague",
        "prompt": "Write code for a database system"
    },
    # ── Conflicting Prompts ──────────────────────────────────────────────────────
    {
        "id": "edge-conflict-1",
        "name": "Conflicting Authentication Rules",
        "type": "conflict",
        "prompt": "Build a secure blog where anyone can edit, update, and delete any post without logging in, but only logged-in users can view posts."
    },
    {
        "id": "edge-conflict-2",
        "name": "Conflicting Role Permissions",
        "type": "conflict",
        "prompt": "Create a hospital portal where doctors can never see patient files, but patients can view all patient records in the entire hospital."
    },
    {
        "id": "edge-conflict-3",
        "name": "Conflicting Payment Engine",
        "type": "conflict",
        "prompt": "Build a subscription SaaS platform that charges users a monthly fee but has no payment options and doesn't allow storing card details or bank details."
    },
    # ── Incomplete Prompts ───────────────────────────────────────────────────────
    {
        "id": "edge-incomplete-1",
        "name": "Incomplete Billing Spec",
        "type": "incomplete",
        "prompt": "Build a SaaS app with subscription billing."
    },
    {
        "id": "edge-incomplete-2",
        "name": "Incomplete Employee Portal",
        "type": "incomplete",
        "prompt": "Create a portal for users to check in."
    },
    {
        "id": "edge-incomplete-3",
        "name": "Incomplete Chat Spec",
        "type": "incomplete",
        "prompt": "Build a messaging room with users."
    }
]
