async function login(event){
    event.preventDefault();

    const userEmail = document.getElementById('userEmail').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/login', {
            method:'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({userEmail, password})
        });

        const data = await response.json();
        console.log(data);
        
    } catch (error) {
        console.log(error);
        
    }

    
}