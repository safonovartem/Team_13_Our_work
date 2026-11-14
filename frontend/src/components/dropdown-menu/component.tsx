interface DropdownMenuProps {
  data: readonly string[];
  value: string | number;
  onChange: (value: string | number) => void;
  disabled?: boolean;
  id?: string;
}

export function DropdownMenu({
  data,
  id,
  value,
  onChange,
  disabled,
}: DropdownMenuProps) {
  return (
    <select
      id={id}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      value={value}
    >
      {data.map((s, i) => {
        return (
          <option key={i} value={s}>
            {s}
          </option>
        );
      })}
    </select>
  );
}
