import { useEffect, useState } from "react";
import { api } from "../api/cliente";
import { formatarData, iniciais } from "../utils/formato";

// A arte do cracha: proporcao de cartao CR80 (54 x 86 mm, o tamanho de um
// cracha de verdade), faixa laranja da marca, marcas de registro nos cantos
// (como peca impressa) e o QR code gerado pela API em SVG.
//
// O QR code vem de GET /cracha/{id}/qrcode.svg, que exige login - por isso
// a imagem e baixada com o token (api.baixarArquivo) e mostrada por um
// endereco temporario do navegador (URL.createObjectURL), em vez de um
// <img src> direto para a API, que iria sem o token.
export function CrachaArte({ cracha, versao = 0 }) {
  const [qr, setQr] = useState(null);

  useEffect(() => {
    let endereco = null;
    let ativo = true;
    api.baixarArquivo(`/cracha/${cracha.estagiario_id}/qrcode.svg`)
      .then((arquivo) => {
        endereco = URL.createObjectURL(arquivo);
        if (ativo) setQr(endereco);
      })
      .catch(() => ativo && setQr(null));
    return () => {
      ativo = false;
      if (endereco) URL.revokeObjectURL(endereco);
    };
  }, [cracha.estagiario_id, cracha.codigo, versao]);

  const codigoCurto = cracha.codigo.slice(0, 8).toUpperCase().replace(/(.{4})/, "$1·");

  return (
    <div className={`cracha${cracha.ativo ? "" : " cracha--inativo"}`}>
      <span className="cracha-furo" aria-hidden="true" />
      <i className="registro registro--te" /><i className="registro registro--td" />
      <i className="registro registro--be" /><i className="registro registro--bd" />

      <div className="cracha-faixa">
        <span>InternHub</span>
        <span>Estágio · Lei 11.788</span>
      </div>

      <div className="cracha-pessoa">
        <div className="cracha-iniciais">{iniciais(cracha.nome)}</div>
        <div className="cracha-matricula">
          <span>matrícula</span>
          <b>{String(cracha.estagiario_id).padStart(5, "0")}</b>
        </div>
      </div>

      <div className="cracha-nome">
        <h2>{cracha.nome}</h2>
        <span>Estagiário</span>
      </div>

      <dl className="cracha-campos">
        <div><dt>Gestor</dt><dd>{cracha.gestor_nome || "—"}</dd></div>
        <div><dt>Desde</dt><dd>{cracha.inicio_estagio ? formatarData(cracha.inicio_estagio) : "—"}</dd></div>
        <div><dt>Emitido</dt><dd>{formatarData(cracha.emitido_em)}</dd></div>
        <div>
          <dt>Situação</dt>
          <dd className={cracha.ativo ? "cracha-ativo" : "cracha-inativo-texto"}><i />{cracha.ativo ? "Ativo" : "Inativo"}</dd>
        </div>
      </dl>

      <div className="cracha-qr">
        {qr ? <img src={qr} alt="QR code de verificação do crachá" /> : <span className="cracha-qr-vazio" />}
        <div>
          <span>verificação</span>
          <b className="mono">{codigoCurto}</b>
          <small>aponte a câmera para conferir o vínculo</small>
        </div>
      </div>
    </div>
  );
}
