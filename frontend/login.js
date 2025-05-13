document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    const errorDiv = document.getElementById("error-message");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();



        try {
            const response = await fetch("http://localhost:8080/token", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({
                    username: username,
                    password: password,
                    grant_type: "password"
                })
            });

             if (!response.ok) {
            errorDiv.textContent = "Invalid credentials";
            errorDiv.style.display = "block";
            return;
        }

            const data = await response.json();
            localStorage.setItem("access_token", data.access_token);
            window.location.href = "/index.html";

        } catch (error) {
            errorDiv.textContent = "Invalid credentials";
            errorDiv.style.display = "block";
        }
    });
});
