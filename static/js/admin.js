async function uploadFile(event) {
    event.preventDefault();
    alert("Uploading file...");
    const form = document.getElementById("fileForm");
    const formData = new FormData(form);
    const messageContainer = document.getElementById("messageContainer");

    try {
        const response = await fetch("/uploadFile", {
            method: "POST",
            body: formData,
        });

        const result = await response.json();

        if (response.ok) {
            messageContainer.style.color = "green";
            messageContainer.textContent = result.message;
        } else {
            messageContainer.style.color = "red";
            messageContainer.textContent = result.message;
        }
    } catch (error) {
        messageContainer.style.color = "red";
        messageContainer.textContent = "An error occurred while uploading the file.";
    }
}