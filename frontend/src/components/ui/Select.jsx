import { forwardRef } from "react";

const Select = forwardRef(function Select(
  { label, hint, className = "", children, ...props },
  ref
) {
  return (
    <label className={["ui-field", className].filter(Boolean).join(" ")}
    >
      {label ? <span className="ui-field__label">{label}</span> : null}
      <select ref={ref} className="ui-select" {...props}>
        {children}
      </select>
      {hint ? <span className="ui-field__hint">{hint}</span> : null}
    </label>
  );
});

export default Select;
