'use babel';

import React from 'react';
import update from 'react/lib/update';
import { DragDropContext } from 'react-dnd';
import HTML5Backend from 'react-dnd-html5-backend';

import {SortableContainer, DbContainer} from './LineList';
import Menu from './Menu';

var app = require('electron').remote;
var dialog = app.dialog;
var fs = require('fs');
var xmlbuilder = require('xmlbuilder');

YAML = require('yamljs');

const knex = require('../db').knex;
const movies_dir = require('../db').movies_dir;

@DragDropContext(HTML5Backend)
export default class Main extends React.Component {

    constructor(props) {
        super(props);

        this.io = {
            save: this.save.bind(this),
            load: this.load.bind(this),
            exp: this.exp.bind(this)
        };
    }

    save() {
        let processLines = (lines) => {
            return lines.map((l) => {
                return {movie: l.title,
                        start: l.start,
                        text: l.text,
                        start_humanized: humanize(l.start)
                }
            });
        }

        let humanize = secs => {
            let s = Math.floor(secs);
            let seconds = s % 60;
            let minutes = ((s-seconds)/60)%60;
            let hours = ((s-seconds-minutes*60)/3600)%60;

            return hours + ":" + minutes + ":" + seconds;
        }

        let dump = YAML.stringify({
            filter: this.refs.aside.state.filter,
            left: processLines(this.refs.left.decoratedComponentInstance.state.lines),
            right: processLines(this.refs.right.decoratedComponentInstance.state.lines)
        });

        dialog.showSaveDialog({
                defaultPath: '~/dialog.yaml'
            },
            function (fileName) {
                if (fileName === undefined){
                    console.log("You didn't save the file");
                    return;
                }
                // fileName is a string that contains the path and filename created in the save file dialog.
                fs.writeFile(fileName, dump, function (err) {
                    if(err){
                        alert("An error ocurred creating the file "+ err.message)
                    }
            });
        });

    }

    load() {
        const that = this;

        let processLines = (lines, target) => {
            target.setState({'lines': []});

            return lines.map(line => {
                knex.from('line')
                    .join('movie', 'movie.id', '=', 'line.movie_id')
                    .select('movie.title',
                        'movie.id',
                        'line.movie_id',
                        'line.start',
                        'line.duration',
                        'line.text',
                        'line.audio',
                        'line.sextimate')
                    .where({
                        'movie.title': line.movie,
                        'line.start': line.start
                    })
                    .limit(1)
                    .then(row => {
                        var lines_ = target.state.lines.slice();
                        lines_.push(row[0]);
                        target.setState({lines: lines_});
                    });
            });
        };

        dialog.showOpenDialog(
            {filters: [
                {name: 'YAML', extensions: ['yaml']}
            ]},
            (filepath) => {
                fs.readFile(filepath[0], 'utf-8', function (err, data) {
                    if(err){
                        alert("An error ocurred reading the file :" + err.message);
                        return;
                    }

                    // Update app states
                    const dump = YAML.parse(data);
                    that.refs.aside.setState({
                        'filter': dump.filter,
                    });

                    processLines(dump.left, that.refs.left.decoratedComponentInstance);
                    processLines(dump.right, that.refs.right.decoratedComponentInstance);

                });
            }
        );

    }

    exp() {
        let name = "testexport";
        var uid = 1;
        var resources = {
            format: [ {
                '@name': 'FFVideoFormat1080p25',
                '@frameDuration': '1/25s',
                '@id': 'r0',
                '@width': 1920,
                '@height': 1080
            } ],
            asset: []
        };

        let links = [];
        let rechts = [];

        var floatToTime = (time, framerate) => {
            let nom_den = framerate.split('/');
            let nom = nom_den[0];
            let den = nom_den[1];

            return Math.round( time*den ) + "/" + den + "s";
        };

        var processLines = (lines, target) => {
            let total_length = 1;
            lines.forEach( line => {
                target.push({
                        '@enabled': 1,
                        '@name': line.text.replace('\n', ' ') + " (" + line.title + " @ " + line.start + ")",
                        '@offset': floatToTime(total_length, line.framerate),
                        '@format': "f" + uid,
                        '@tcFormat': "NDF",
                        '@duration': floatToTime(line.duration, line.framerate),
                        '@start': floatToTime(line.start, line.framerate),
                        video: {
                            '@ref': "r" + uid,
                            '@offset': "0/1s",
                            '@start': "0/1s",
                            '@duration': floatToTime(line.total_duration, line.framerate),
                            audio: {
                                '@ref': "r" + uid,
                                '@lane': "-1",
                                '@offset': "0/1s",
                                '@duration': floatToTime(line.total_duration, line.framerate),
                                '@srcCh': "1, 2", // TODO checken!!
                            }
                        }
                }); // push

                resources.asset.push({
                    '@hasVideo': 1,
                    '@name': line.title,
                    '@format': "f"+uid,
                    '@hasAudio': 1,
                    '@id': "r"+uid,
                    '@audioSources': 1,
                    '@audioChannels': 2,
                    '@src': encodeURI("file://" + movies_dir + "/" + line.video),
                    '@duration': floatToTime(line.total_duration, line.framerate),
                    '@start': "0/1s"
                });

                resources.format.push({
                    '@name': "FFVideoFormatRateUndefined",
                    '@frameDuration': line.framerate,
                    '@id': "f"+uid,
                    '@width': line.width,
                    '@height': line.height
                });

                uid += 1;
                total_length += line.duration;

            }); // forEach line
            return floatToTime(total_length, "1000/1000");
        };

        let duration_links = processLines(this.refs.left.decoratedComponentInstance.state.lines, links);
        let duration_rechts = processLines(this.refs.right.decoratedComponentInstance.state.lines, rechts);


        let obj = {
            fcpxml: {
                '@version': 1.5,
                resources,
                library: {
                    event: {
                        '@name': name,
                        project: [{
                            '@name': 'links',
                            sequence: {
                                '@format': 'r0',
                                '@tcFormat': 'NDF',
                                '@duration': duration_links,
                                spine: { clip: links }
                            }
                        }, {
                            '@name': 'rechts',
                            sequence: {
                                '@format': 'r0',
                                '@tcFormat': 'NDF',
                                '@duration': duration_rechts,
                                spine: { clip: rechts }
                            }
                        } ]
                    }
                }
            }
        }

        let doc = xmlbuilder.create(obj).end({pretty: true});
        dialog.showSaveDialog({
                defaultPath: '~/dialog.fcpxml'
            },
            function (fileName) {
                if (fileName === undefined){
                    console.log("You didn't save the file");
                    return;
                }
                // fileName is a string that contains the path and filename created in the save file dialog.
                fs.writeFile(fileName, doc, function (err) {
                    if(err){
                        alert("An error occurred creating the file "+ err.message)
                    }
                });
            });

    }

    render() {
        return <div>
            <Aside io={this.io} ref="aside"/>
            <main>
                <SortableContainer ref="left"/>
                <SortableContainer ref="right"/>
            </main>
        </div>;
    }
}

class Aside extends React.Component {
    constructor(){
        super();
        this.state = {filter: ''};
    }
    update = (e) => {
        this.setState({filter: this.refs.filterInput.value});
    }
    render() {
        return <aside>
            <Menu io={this.props.io}/>

            <input  type="search"
                    placeholder="Dialogsuche…"
                    ref="filterInput"
                    id="filter"
                    value={this.state.filter}
                    onChange={this.update} />
            <DbContainer filter={this.state.filter}/>
        </aside>;
    }
}
