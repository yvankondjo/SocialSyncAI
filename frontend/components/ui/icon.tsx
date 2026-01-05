import Image from "next/image"

interface IconProps {
  name: string
  className?: string
}

export function Icon({ name, className = "w-5 h-5" }: IconProps) {
  return (
    <Image
      src={`/icons/${name}.svg`}
      alt={name}
      width={20}
      height={20}
      className={className}
    />
  )
}