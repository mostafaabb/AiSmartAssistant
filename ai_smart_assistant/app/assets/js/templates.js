/**
 * Code Templates for All Supported Languages
 * Provides starter code snippets for quick project initialization
 */

const CodeTemplates = {
    // ==================== PYTHON ====================
    'python-basic': {
        name: 'Python Script',
        language: 'python',
        code: `#!/usr/bin/env python3
"""
A simple Python script template.
"""

def main():
    """Main entry point."""
    print("Hello, World!")
    # Add your code here

if __name__ == "__main__":
    main()
`
    },
    
    'python-class': {
        name: 'Python Class',
        language: 'python',
        code: `#!/usr/bin/env python3
"""
Python class template with common methods.
"""

class MyClass:
    """A sample class."""
    
    def __init__(self, name: str):
        """Initialize the class."""
        self.name = name
    
    def greet(self) -> str:
        """Return a greeting."""
        return f"Hello, {self.name}!"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"MyClass(name={self.name!r})"

if __name__ == "__main__":
    obj = MyClass("Python")
    print(obj.greet())
`
    },
    
    // ==================== JAVASCRIPT ====================
    'js-fetch': {
        name: 'JavaScript Fetch API',
        language: 'javascript',
        code: `/**
 * Fetch API example - Making HTTP requests
 */

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(\`HTTP error! status: \${response.status}\`);
        }
        const data = await response.json();
        console.log('Data:', data);
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

// Usage
fetchData('https://api.github.com/users/github');
`
    },
    
    'js-async': {
        name: 'JavaScript Async/Await',
        language: 'javascript',
        code: `/**
 * Async/Await pattern example
 */

async function processData() {
    try {
        console.log('Starting...');
        
        // Simulate async operations
        await new Promise(resolve => setTimeout(resolve, 1000));
        console.log('Step 1 complete');
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        console.log('Step 2 complete');
        
        return 'All done!';
    } catch (error) {
        console.error('Error:', error);
    }
}

// Call the async function
processData().then(result => console.log(result));
`
    },
    
    // ==================== TYPESCRIPT ====================
    'ts-class': {
        name: 'TypeScript Class',
        language: 'typescript',
        code: `/**
 * TypeScript class with type annotations
 */

interface User {
    id: number;
    name: string;
    email: string;
}

class UserManager {
    private users: User[] = [];
    
    addUser(user: User): void {
        this.users.push(user);
    }
    
    getUser(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }
    
    getAllUsers(): User[] {
        return this.users;
    }
}

const manager = new UserManager();
manager.addUser({ id: 1, name: 'John', email: 'john@example.com' });
console.log(manager.getAllUsers());
`
    },
    
    // ==================== HTML ====================
    'html-basic': {
        name: 'HTML Boilerplate',
        language: 'html',
        code: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Website</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f4f4f4;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome!</h1>
        <p>This is a basic HTML template.</p>
    </div>
</body>
</html>
`
    },
    
    // ==================== CSS ====================
    'css-grid': {
        name: 'CSS Grid Layout',
        language: 'css',
        code: `/* CSS Grid Example */

.grid-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding: 20px;
    background: #f0f0f0;
    min-height: 100vh;
}

.grid-item {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.grid-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

@media (max-width: 768px) {
    .grid-container {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .grid-container {
        grid-template-columns: 1fr;
    }
}
`
    },
    
    // ==================== JAVA ====================
    'java-main': {
        name: 'Java Main Program',
        language: 'java',
        code: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        
        // Your code here
        int number = 42;
        System.out.println("Number: " + number);
    }
}
`
    },
    
    'java-class': {
        name: 'Java Class',
        language: 'java',
        code: `public class Person {
    private String name;
    private int age;
    
    // Constructor
    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    // Getters
    public String getName() {
        return name;
    }
    
    public int getAge() {
        return age;
    }
    
    // Method
    public void displayInfo() {
        System.out.println("Name: " + name + ", Age: " + age);
    }
    
    // Main method
    public static void main(String[] args) {
        Person p = new Person("John", 30);
        p.displayInfo();
    }
}
`
    },
    
    // ==================== C++ ====================
    'cpp-main': {
        name: 'C++ Program',
        language: 'cpp',
        code: `#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    
    int number = 42;
    cout << "Number: " << number << endl;
    
    return 0;
}
`
    },
    
    // ==================== RUST ====================
    'rust-main': {
        name: 'Rust Program',
        language: 'rust',
        code: `fn main() {
    println!("Hello, World!");
    
    let number = 42;
    println!("Number: {}", number);
    
    // Iterate
    for i in 1..=5 {
        println!("Count: {}", i);
    }
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}
`
    },
    
    // ==================== GO ====================
    'go-main': {
        name: 'Go Program',
        language: 'go',
        code: `package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
    
    number := 42
    fmt.Println("Number:", number)
    
    result := add(10, 20)
    fmt.Println("Sum:", result)
}

func add(a, b int) int {
    return a + b
}
`
    },
    
    // ==================== SQL ====================
    'sql-query': {
        name: 'SQL Query',
        language: 'sql',
        code: `-- SQL Query Example

-- Create table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert data
INSERT INTO users (name, email) VALUES 
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com');

-- Select query
SELECT * FROM users WHERE name LIKE 'John%';

-- Join example
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;
`
    },
    
    // ==================== FLASK ====================
    'flask-api': {
        name: 'Flask REST API',
        language: 'python',
        code: `from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data
users = [
    {'id': 1, 'name': 'John', 'email': 'john@example.com'},
    {'id': 2, 'name': 'Jane', 'email': 'jane@example.com'}
]

@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the API'})

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    new_user = {
        'id': len(users) + 1,
        'name': data.get('name'),
        'email': data.get('email')
    }
    users.append(new_user)
    return jsonify(new_user), 201

if __name__ == '__main__':
    print("Server running on http://127.0.0.1:5001")
    app.run(debug=False, port=5001)
`
    },
    
    // ==================== EXPRESS ====================
    'express-app': {
        name: 'Express.js Server',
        language: 'javascript',
        code: `const express = require('express');
const app = express();
const PORT = 3001;

// Middleware
app.use(express.json());

// Sample data
let users = [
    { id: 1, name: 'John', email: 'john@example.com' },
    { id: 2, name: 'Jane', email: 'jane@example.com' }
];

// Routes
app.get('/', (req, res) => {
    res.json({ message: 'Welcome to Express API' });
});

app.get('/users', (req, res) => {
    res.json(users);
});

app.get('/users/:id', (req, res) => {
    const user = users.find(u => u.id === parseInt(req.params.id));
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
});

app.post('/users', (req, res) => {
    const newUser = {
        id: users.length + 1,
        name: req.body.name,
        email: req.body.email
    };
    users.push(newUser);
    res.status(201).json(newUser);
});

app.listen(PORT, () => {
    console.log(\`Server running on http://localhost:\${PORT}\`);
});
`
    },
    
    // ==================== RUBY ====================
    'ruby-main': {
        name: 'Ruby Program',
        language: 'ruby',
        code: `#!/usr/bin/env ruby
# Ruby program template

def greet(name)
  "Hello, \#{name}!"
end

def add(a, b)
  a + b
end

# Main execution
puts greet("Ruby")
puts "Sum: \#{add(10, 20)}"

# Array iteration
numbers = [1, 2, 3, 4, 5]
numbers.each { |n| puts "Number: \#{n}" }
`
    },
    
    // ==================== PHP ====================
    'php-basic': {
        name: 'PHP Script',
        language: 'php',
        code: `<?php
/**
 * Basic PHP template
 */

function greet(\$name) {
    return "Hello, \$name!";
}

function add(\$a, \$b) {
    return \$a + \$b;
}

// Main execution
echo greet("PHP") . "\\n";
echo "Sum: " . add(10, 20) . "\\n";

// Array operations
\$numbers = [1, 2, 3, 4, 5];
foreach (\$numbers as \$num) {
    echo "Number: \$num\\n";
}
?>
`
    },
    
    // ==================== SHELL ====================
    'bash-script': {
        name: 'Bash Script',
        language: 'bash',
        code: `#!/bin/bash
# Bash script template

echo "Hello, World!"

# Variables
name="User"
echo "Welcome, \$name!"

# Function
greet() {
    echo "Greeting from function: \$1"
}

greet "Alice"

# Loop
for i in {1..5}; do
    echo "Number: \$i"
done

# Conditional
number=10
if [ \$number -gt 5 ]; then
    echo "Number is greater than 5"
else
    echo "Number is 5 or less"
fi
`
    },
    
    // ==================== JSON ====================
    'json-example': {
        name: 'JSON Example',
        language: 'json',
        code: `{
  "project": "NexusAI",
  "version": "2.0.0",
  "description": "Intelligent Code Assistant",
  "author": "Your Name",
  "settings": {
    "theme": "dark",
    "fontSize": 14,
    "autoSave": true
  },
  "languages": [
    "python",
    "javascript",
    "typescript",
    "java",
    "cpp",
    "rust",
    "go"
  ],
  "features": {
    "codeExecution": true,
    "aiAssistance": true,
    "livePreview": true,
    "codeMetrics": true
  }
}
`
    },
    
    // ==================== MARKDOWN ====================
    'md-readme': {
        name: 'README Markdown',
        language: 'markdown',
        code: `# Project Title

> A brief description of your project.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

\`\`\`bash
npm install
# or
pip install -r requirements.txt
\`\`\`

## Usage

\`\`\`python
import mymodule
mymodule.run()
\`\`\`

## Contributing

1. Fork the repository
2. Create a feature branch (\`git checkout -b feature/AmazingFeature\`)
3. Commit your changes (\`git commit -m 'Add AmazingFeature'\`)
4. Push to the branch (\`git push origin feature/AmazingFeature\`)
5. Open a Pull Request

## License

MIT License
`
    }
};

// Load template into editor
function loadTemplate(templateKey) {
    const template = CodeTemplates[templateKey];
    if (template) {
        const editor = EditorManager.instance || window.editor;
        if (editor) {
            editor.setValue(template.code);
            EditorManager.setLanguage(template.language);
            document.getElementById('language-select').value = template.language;
            NexusAI.state.currentFile = \`\${templateKey}.\${getFileExtension(template.language)}\`;
            Toast.success(\`Loaded: \${template.name}\`);
        }
    }
}

// Helper function to get file extension
function getFileExtension(language) {
    const extensions = {
        'python': 'py',
        'javascript': 'js',
        'typescript': 'ts',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'rust': 'rs',
        'go': 'go',
        'ruby': 'rb',
        'php': 'php',
        'bash': 'sh',
        'html': 'html',
        'css': 'css',
        'json': 'json',
        'sql': 'sql',
        'markdown': 'md',
        'csharp': 'cs'
    };
    return extensions[language] || 'txt';
}

// Initialize template buttons
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.template-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const templateKey = e.target.dataset.template;
            if (templateKey) {
                loadTemplate(templateKey);
            }
        });
    });
});
