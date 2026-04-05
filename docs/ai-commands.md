# 🤖 AI Chat Tool – Configuration Commands

The Maverick Scheduler includes an AI-powered configuration assistant that allows you to modify the system using natural language.

This tool translates user commands into safe, structured backend operations using predefined system functions.

---

## 🚀 How It Works

1. Enter a natural-language command in the AI Chat interface
2. The AI interprets your intent
3. A predefined tool is selected and executed
4. The configuration is updated safely

⚠️ The system is **stateless** — each command is processed independently.

---

## 🧠 Command Guidelines

To ensure successful execution:

- Be **clear and specific**
- Use **exact names** when possible (course IDs, rooms, labs, faculty)
- Include all required details (e.g., credits, new names, etc.)

### ✅ Good Examples
- Change the credits of CS199 to 4  
- Rename course CS163 to CS370  
- Add room Roddy 150  

### ❌ Avoid
- Change CS199  
- Update Hardy  
- Fix the room  

---

# 📚 Supported Commands

---

## 👨‍🏫 Faculty Management

### Add Faculty
- Add faculty Dr. Jones with appointment type full-time  
- Add faculty Hardy with appointment type adjunct  

### Remove Faculty
- Remove faculty Dr. Jones  
- Delete faculty Hardy  

### Modify Faculty
- Change faculty Hardy minimum credits to 10  
- Change faculty Hardy maximum credits to 14  
- Change faculty Hardy unique course limit to 3  
- Change faculty Hardy appointment type to full-time  
- Update faculty Hardy day to MON from 10:00-18:00 
- Make Hardy unavailable on MON

---

## 🏫 Room Management

### Add Room
- Add room Roddy 150  
- Create room Room A  

### Remove Room
- Remove room Roddy 150  
- Delete room Room A  

### Rename Room
- Rename room Roddy 150 to Roddy 151  
- Change room Room A to Room B  

---

## 🧪 Lab Management

### Add Lab
- Add lab Linux  
- Create lab Windows  

### Remove Lab
- Remove lab Linux  
- Delete lab Mac  

### Rename Lab
- Rename lab Linux to PC Lab  
- Change lab Mac to Apple Lab  

---

## 📖 Course Management

### Add Course
- Add course CS103 with 3 credits in Roddy 151 with no lab and no faculty
- Add course CMSC 410 with 4 credits in Room A with lab Apple Lab and with faculty Dr. Jones and Hardy  

### Remove Course
- Remove course CS102  
- Delete course CMSC 410  

---

### ✏️ Modify Courses

#### Rename Course
- Rename course CS163 to CS370  
- Change course ID CS102 to CS202  

#### Change Credits
- Change the credits of CS199 to 4  
- Set CS102 credits to 3  

#### Change Room
- Change the room for CS199 to Roddy 147  
- Move CS102 to Roddy 140  

#### Change Lab
- Change the lab for CS199 to Linux  
- Set CS102 lab to Mac  
- Delete the lab for CS102

#### Change Faculty
- Set the faculty for CS199 to Hardy  
- Assign Hardy and Xie to CS199  

#### Change Conflicts
- Set the conflicts for CS199 to CMSC 330  
- Set the conflicts for CS199 to CMSC 330 and CMSC 362  

---

## ⚠️ Conflict Management

### Add Conflict
- Add a conflict between CS101 and CS102  
- Create a conflict between CMSC 140 and CMSC 161  

### Remove Conflict
- Remove the conflict between CS101 and CS102  
- Delete the conflict between CS199 and CMSC 330  

### Modify Conflict
- Change conflict on CS101 from CS102 to CS103  
- Replace the conflict on CS199 from CMSC 330 to CMSC 362  

---

# 🧩 Supported AI Tools

The AI system uses the following backend tools:

- `add_course`
- `remove_course`
- `rename_course`
- `modify_course_credits`
- `modify_course_room`
- `modify_course_lab`
- `remove_course_lab`
- `modify_course_faculty`
- `modify_course_conflicts`
- `add_faculty`
- `remove_faculty`
- `modify_faculty`
- `set_faculty_day_unavailable_tool`
- `add_room`
- `remove_room`
- `rename_room`
- `add_lab`
- `remove_lab`
- `rename_lab`
- `add_conflict`
- `remove_conflict`
- `modify_conflict`

---

# ⚡ Tips for Best Results

- Always include **all required values**
- Prefer **explicit wording** over shorthand
- Think of commands as:
  
  👉 *“Action + Entity + Details”*

Example:
> Change the credits of CS199 to 4

---

# 🔒 Safety Design

The AI system is designed to be:

- **Safe** → only predefined tools can execute changes  
- **Predictable** → no arbitrary code execution  
- **Stateless** → no hidden memory between commands  

---

# 🧪 Example Workflow

1. Add course CS199 with 4 credits in Roddy 140  
2. Assign Hardy and Xie to CS199  
3. Change the credits of CS199 to 3  
4. Rename course CS199 to CS299  

Each step is processed independently and safely applied.