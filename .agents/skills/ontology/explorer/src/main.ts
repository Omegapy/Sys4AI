import {captureFragment} from './api';
import {ExplorerApp} from './app';
import {ProjectApp} from './project-app';
import {captureProjectFragment} from './project-api';
const projectMode=new URLSearchParams(location.search).get('app')==='1';
const initial=projectMode?captureProjectFragment():captureFragment();
const root=document.getElementById('app')!;
const app=projectMode?new ProjectApp(root,import.meta.env.EXPLORER_BUILD_ID as string,import.meta.env.EXPLORER_SCHEMA_SHA256 as string):new ExplorerApp(root,import.meta.env.EXPLORER_BUILD_ID as string,import.meta.env.EXPLORER_SCHEMA_SHA256 as string);
void app.start(initial);
