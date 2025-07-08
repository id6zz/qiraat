let mediaRecorder;
let recordedChunks = [];

document.getElementById("start").addEventListener("click", async () => {
  recordedChunks = [];

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.ondataavailable = event => {
    if (event.data.size > 0) recordedChunks.push(event.data);
  };

  mediaRecorder.onstop = async () => {
    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append("file", blob, "recording.webm");

    const response = await fetch("/reverse_search", {
      method: "POST",
      body: formData
    });

    const result = await response.json();
    document.getElementById("result").innerText = 
      result.best_match ? `✅ Match: ${result.best_match}` : "❌ No match found";
  };

  mediaRecorder.start();
  setTimeout(() => mediaRecorder.stop(), 3000); // Record 3 sec
});
