import React from 'react';

export default function UserProfile() {
  // PII VULNERABILITY: Unmasked user email and phone in the source code
  const userEmail = "john.doe@example.com";
  const userPhone = "+1-555-019-8472";

  return (
    <div>
      <h1>User Profile</h1>
      <p>Email: {userEmail}</p>
      <p>Phone: {userPhone}</p>
    </div>
  );
}