interface DropdownMenuProps {
  data: string[];
  id?: string;
}

export function DropdownMenu({ data, id }: DropdownMenuProps) {
  return (
    <select id={id}>
      {data.map((s, i) => {
        return <option key={i}>{s}</option>;
      })}
    </select>
  );
}
