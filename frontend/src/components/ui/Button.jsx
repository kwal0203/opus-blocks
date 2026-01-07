import { forwardRef } from "react";

const Button = forwardRef(function Button(
  { variant = "default", size = "md", className = "", ...props },
  ref
) {
  const classes = [
    "ui-button",
    `ui-button--${variant}`,
    `ui-button--${size}`,
    className
  ]
    .filter(Boolean)
    .join(" ");

  return <button ref={ref} className={classes} {...props} />;
});

export default Button;
