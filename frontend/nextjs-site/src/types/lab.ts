export type LabFramework = 'streamlit' | 'gradio'

export type LabType =
  | 'visualization'
  | 'parameter-tuning'
  | 'training-demo'
  | 'dataset-experiment'

export interface Lab {
  id: number
  algorithm_id: number
  lab_name: string
  lab_type: LabType
  url: string | null
  framework: LabFramework
}
