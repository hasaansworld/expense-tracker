import React from "react";

const Card = ({ children, className = "" }) => {
  return (
    <div
      className={`p-6 rounded-lg shadow-sm border border-gray-100 ${className}`}
    >
      {children}
    </div>
  );
};

export default Card;
