import { forwardRef } from "react";

const Textarea = forwardRef(function Textarea(
  { label, hint, className = "", ...props },
  ref
) {
  return (
    <label className={["ui-field", className].filter(Boolean).join(" ")}
    >
      {label ? <span className="ui-field__label">{label}</span> : null}
      <textarea ref={ref} className="ui-textarea" {...props} />
      {hint ? <span className="ui-field__hint">{hint}</span> : null}
    </label>
  );
});

export default Textarea;
