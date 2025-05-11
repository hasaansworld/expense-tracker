import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function Input({
  label,
  type = "text",
  id,
  name,
  value,
  onChange,
  placeholder = "",
  required = false,
  className = "",
  ...props
}) {
  const [inputType, setInputType] = useState(type);
  const [isFocused, setIsFocused] = useState(false);

  const isPassword = type === "password";

  const togglePasswordVisibility = () => {
    setInputType(inputType === "password" ? "text" : "password");
  };

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label
          htmlFor={id}
          className="block mb-2 capitalize text-sm font-medium text-gray-700 text-start"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        <input
          type={inputType}
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          className={`w-full px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md focus:outline-none ${
            isFocused ? "ring-2 ring-blue-500 border-blue-500" : ""
          }`}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />

        {isPassword && (
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-600"
            tabIndex="-1"
          >
            {inputType === "password" ? (
              <Eye size={20} />
            ) : (
              <EyeOff size={20} />
            )}
          </button>
        )}
      </div>
    </div>
  );
}
