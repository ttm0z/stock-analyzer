import React, { useState } from 'react';

function SendMessage() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const sendMessage = async () => {
    if (!message) return alert('Please enter a message.');

    try {
      const res = await fetch('http://localhost:5000/test/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();
      if (res.ok) {
        setResponse(data.message);
        setMessage('');
      } else {
        setResponse(data.error || 'Error sending message');
      }
    } catch (err) {
      setResponse('Network error');
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Type your message here"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <button onClick={sendMessage}>Send</button>

      {response && <p>{response}</p>}
    </div>
  );
}

export default SendMessage;
