import {captureFragment} from './api';
import {ExplorerApp} from './app';
const initial=captureFragment();
const root=document.getElementById('app')!;
const app=new ExplorerApp(root,import.meta.env.EXPLORER_BUILD_ID as string,import.meta.env.EXPLORER_SCHEMA_SHA256 as string);
void app.start(initial);
