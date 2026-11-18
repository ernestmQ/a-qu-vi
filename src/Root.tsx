import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { Props } from "./l11/lib";
import { COMPS } from "./pk";

const FPS = 30;
const calcular: CalculateMetadataFunction<Props> = ({ props }) => ({ durationInFrames: Math.ceil((props.manifest.duration + 1.2) * FPS) });
const comun = { fps: FPS, width: 1920, height: 1080, durationInFrames: 60 * FPS, calculateMetadata: calcular };

export const RemotionRoot: React.FC = () => (
  <>{COMPS.map((c) => <Composition key={c.id} id={c.id} component={c.component as React.FC<Props>} {...comun} defaultProps={{ manifest: c.manifest, audio: null, etiqueta: "" } as Props} />)}</>
);
