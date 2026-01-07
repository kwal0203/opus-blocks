import { forwardRef } from "react";

const Input = forwardRef(function Input(
  { label, hint, className = "", ...props },
  ref
) {
  return (
    <label className={["ui-field", className].filter(Boolean).join(" ")}
    >
      {label ? <span className="ui-field__label">{label}</span> : null}
      <input ref={ref} className="ui-input" {...props} />
      {hint ? <span className="ui-field__hint">{hint}</span> : null}
    </label>
  );
});

export default Input;
