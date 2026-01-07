const Toast = ({ variant = "default", title, message, onClose }) => {
  const classes = ["ui-toast", `ui-toast--${variant}`].join(" ");

  return (
    <div className={classes} role="status">
      <div>
        {title ? <strong className="ui-toast__title">{title}</strong> : null}
        {message ? <p className="ui-toast__message">{message}</p> : null}
      </div>
      {onClose ? (
        <button className="ui-toast__close" type="button" onClick={onClose}>
          Close
        </button>
      ) : null}
    </div>
  );
};

export default Toast;
