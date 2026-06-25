import { useEffect, useState } from 'react'
import { api } from '../lib/api'

type Props = {
  url: string
  onOpen?: (src: string) => void
}

// Картинка-вложение в пузыре переписки. Тег <img> не умеет слать Authorization,
// поэтому грузим файл через fetch с initData и показываем object URL, освобождая
// его при размонтировании.
export default function AttachmentImage({ url, onOpen }: Props) {
  const [src, setSrc] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let revoked = false
    let objectUrl: string | null = null
    api
      .attachment(url)
      .then((blobUrl) => {
        if (revoked) {
          URL.revokeObjectURL(blobUrl)
          return
        }
        objectUrl = blobUrl
        setSrc(blobUrl)
      })
      .catch(() => setFailed(true))
    return () => {
      revoked = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [url])

  if (failed) return <div className="bubble__img-fail">Не удалось загрузить изображение</div>
  if (!src) return <div className="bubble__img-skeleton" />

  return (
    <img
      className="bubble__img"
      src={src}
      alt="Вложение"
      loading="lazy"
      onClick={() => onOpen?.(src)}
    />
  )
}
